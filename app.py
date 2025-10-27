"""
Ashley AI - FastAPI Backend Server
A voice-controlled AI assistant with enhanced NLP capabilities
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
import base64
import io
import tempfile
import os
from typing import Dict, List, Optional
from datetime import datetime
import uuid

# Import Ashley AI modules
from config import get_config
from nlp_processor import get_intent_hybrid, get_intent_with_context, extract_entities
from tts import speak, cleanup as tts_cleanup
from stt import take_command, calibrate_microphone, get_microphone_source
from weather_utils import handle_temperature, handle_weather
from SearchNow import search_google, search_youtube, search_wikipedia
from Dictapp import openappweb, closeappweb
from alarm import create_event, list_alarms, cancel_alarm, set_alarm_voice
from error_handler import handle_errors, APIError

# Initialize FastAPI app
app = FastAPI(
    title="Ashley AI Assistant",
    description="A voice-controlled AI assistant with enhanced NLP capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration
config = get_config()

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.get('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.get('LOG_FILE', 'assistant.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global conversation history for context awareness
conversation_history: Dict[str, List[str]] = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_sessions: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if client_id:
            self.user_sessions[client_id] = websocket
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, client_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if client_id and client_id in self.user_sessions:
            del self.user_sessions[client_id]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# Pydantic models for request/response
from pydantic import BaseModel

class VoiceCommandRequest(BaseModel):
    text: str
    client_id: Optional[str] = None
    use_context: bool = True

class VoiceCommandResponse(BaseModel):
    intent: str
    confidence: float
    entities: Dict
    response: str
    success: bool
    error: Optional[str] = None

class TextToSpeechRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-US-MichelleNeural"
    use_ssml: bool = False

class AlarmRequest(BaseModel):
    time_input: str
    label: str = "Voice Alarm"

class SearchRequest(BaseModel):
    query: str
    search_type: str = "google"  # google, youtube, wikipedia

class AppControlRequest(BaseModel):
    app_name: str
    action: str = "open"  # open, close

# Helper functions
def get_user_history(client_id: str) -> List[str]:
    """Get conversation history for a specific client"""
    return conversation_history.get(client_id, [])

def add_to_history(client_id: str, text: str):
    """Add text to conversation history"""
    if client_id not in conversation_history:
        conversation_history[client_id] = []
    
    conversation_history[client_id].append(text)
    
    # Keep only last 10 interactions
    if len(conversation_history[client_id]) > 10:
        conversation_history[client_id].pop(0)

@handle_errors(speak_error=False, default_return="I encountered an error processing your request.")
def process_voice_command(text: str, client_id: str = None, use_context: bool = True) -> Dict:
    """Process voice command and return response"""
    try:
        # Get conversation history if context is enabled
        history = get_user_history(client_id) if use_context and client_id else None
        
        # Enhanced intent detection with context
        if use_context and history:
            intent, confidence, entities = get_intent_with_context(text, history)
        else:
            intent, confidence, entities = get_intent_hybrid(text)
        
        logger.info(f"Detected intent: {intent} (confidence: {confidence:.2f})")
        logger.info(f"Extracted entities: {entities}")
        
        # Add to conversation history
        if client_id:
            add_to_history(client_id, text)
        
        # Process intent and generate response
        response = process_intent(intent, text, entities)
        
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "response": response,
            "success": True,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "entities": {},
            "response": "I encountered an error processing your request.",
            "success": False,
            "error": str(e)
        }

def process_intent(intent: str, text: str, entities: Dict) -> str:
    """Process specific intent and return response"""
    try:
        if intent == "exit":
            return "Alright, have a great day! I'm just a call away."
        
        elif intent in ["greet", "smalltalk_hello"]:
            hour = datetime.now().hour
            if 0 <= hour <= 12:
                return "Good Morning, sir. Welcome back! How can I help you today?"
            elif 12 < hour <= 18:
                return "Good Afternoon, sir. Welcome back! How can I help you today?"
            else:
                return "Good Evening, sir. Welcome back! How can I help you today?"
        
        elif intent in ["get_name", "get_capabilities"]:
            if intent == "get_name":
                return f"I'm {config.get('ASSISTANT_NAME')}, your AI assistant."
            else:
                return "I can help you with weather, search, alarms, app control, and much more. Just ask!"
        
        elif intent in ["smalltalk_howareyou", "smalltalk_ok", "thanks", "compliment"]:
            if intent == "smalltalk_howareyou":
                return "I'm doing great, thank you for asking! How can I help you today?"
            elif intent == "thanks":
                return "You're very welcome! Is there anything else I can help you with?"
            elif intent == "compliment":
                return "Thank you so much! That's very kind of you to say."
            else:
                return "That's wonderful to hear! How can I assist you today?"
        
        elif intent in ["search_google", "general_search"]:
            search_query = entities.get("search_query", [text])[0] if entities.get("search_query") else text
            return f"Searching Google for: {search_query}"
        
        elif intent == "search_youtube":
            search_query = entities.get("search_query", [text])[0] if entities.get("search_query") else text
            return f"Searching YouTube for: {search_query}"
        
        elif intent == "search_wikipedia":
            search_query = entities.get("search_query", [text])[0] if entities.get("search_query") else text
            return f"Searching Wikipedia for: {search_query}"
        
        elif intent in ["temperature", "weather", "weather_extended"]:
            if intent == "temperature":
                return "Getting temperature information for you."
            else:
                return "Getting weather information for you."
        
        elif intent in ["get_time", "get_date", "get_datetime"]:
            now = datetime.now()
            if intent == "get_time":
                strTime = now.strftime("%I:%M %p")
                return f"Sir, the time is {strTime}"
            elif intent == "get_date":
                strDate = now.strftime("%A, %B %d, %Y")
                return f"Today is {strDate}"
            else:  # get_datetime
                strTime = now.strftime("%I:%M %p")
                strDate = now.strftime("%A, %B %d, %Y")
                return f"Sir, today is {strDate} and the time is {strTime}"
        
        elif intent in ["open_app", "app_control"]:
            app_name = entities.get("app_name", [text])[0] if entities.get("app_name") else text
            return f"Opening {app_name} for you."
        
        elif intent == "close_app":
            app_name = entities.get("app_name", [text])[0] if entities.get("app_name") else text
            return f"Closing {app_name} for you."
        
        elif intent in ["set_alarm", "list_alarms", "cancel_alarm"]:
            if intent == "set_alarm":
                return "I'll help you set an alarm. Please provide the time."
            elif intent == "list_alarms":
                return "Let me check your alarms for you."
            elif intent == "cancel_alarm":
                return "Which alarm would you like to cancel?"
        
        elif intent == "help":
            return "I can help you with weather, search the web, set alarms, control apps, tell time, and much more. Just ask me anything!"
        
        elif intent == "repeat":
            return "I don't have anything to repeat yet."
        
        else:
            return "I'm not sure how to help with that. Could you try rephrasing your request?"
    
    except Exception as e:
        logger.error(f"Error processing intent {intent}: {e}")
        return "I encountered an error processing that request."

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Ashley AI Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "voice_command": "/api/voice-command",
            "text_to_speech": "/api/tts",
            "search": "/api/search",
            "alarm": "/api/alarm",
            "app_control": "/api/app-control",
            "websocket": "/ws"
        }
    }

@app.post("/api/voice-command", response_model=VoiceCommandResponse)
async def voice_command(request: VoiceCommandRequest):
    """Process voice command and return intent analysis and response"""
    try:
        result = process_voice_command(
            text=request.text,
            client_id=request.client_id,
            use_context=request.use_context
        )
        return VoiceCommandResponse(**result)
    except Exception as e:
        logger.error(f"Error in voice command endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
async def text_to_speech(request: TextToSpeechRequest):
    """Convert text to speech and return audio file"""
    try:
        # Generate unique filename
        audio_id = str(uuid.uuid4())
        audio_file = f"temp_audio_{audio_id}.mp3"
        
        # Use TTS function to generate audio
        speak(request.text, voice=request.voice, use_ssml=request.use_ssml)
        
        # For now, return success message
        # In a real implementation, you'd return the audio file
        return {
            "success": True,
            "message": "Text converted to speech",
            "audio_id": audio_id,
            "text": request.text
        }
    except Exception as e:
        logger.error(f"Error in TTS endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search(request: SearchRequest):
    """Perform web search"""
    try:
        if request.search_type == "google":
            search_google(request.query)
            return {"success": True, "message": f"Google search performed for: {request.query}"}
        elif request.search_type == "youtube":
            search_youtube(request.query)
            return {"success": True, "message": f"YouTube search performed for: {request.query}"}
        elif request.search_type == "wikipedia":
            search_wikipedia(request.query)
            return {"success": True, "message": f"Wikipedia search performed for: {request.query}"}
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alarm")
async def alarm_control(request: AlarmRequest):
    """Set or manage alarms"""
    try:
        if request.time_input.lower() in ["list", "show"]:
            list_alarms()
            return {"success": True, "message": "Alarm list retrieved"}
        else:
            # Set alarm
            success = set_alarm_voice(request.time_input, request.label)
            if success:
                return {"success": True, "message": f"Alarm '{request.label}' set for {request.time_input}"}
            else:
                return {"success": False, "message": "Failed to set alarm"}
    except Exception as e:
        logger.error(f"Error in alarm endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/app-control")
async def app_control(request: AppControlRequest):
    """Control applications"""
    try:
        if request.action == "open":
            openappweb(request.app_name)
            return {"success": True, "message": f"Opening {request.app_name}"}
        elif request.action == "close":
            closeappweb(request.app_name)
            return {"success": True, "message": f"Closing {request.app_name}"}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except Exception as e:
        logger.error(f"Error in app control endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weather")
async def get_weather(city: str = None):
    """Get weather information"""
    try:
        if city:
            # Get weather for specific city
            from weather_utils import get_openweather_data, speak_weather
            data = get_openweather_data(city)
            if data:
                return {"success": True, "weather": data, "city": city}
            else:
                return {"success": False, "message": "Could not fetch weather data"}
        else:
            # Get weather for current location
            from weather_utils import get_location, get_openweather_data
            location = get_location()
            data = get_openweather_data(location)
            if data:
                return {"success": True, "weather": data, "city": location}
            else:
                return {"success": False, "message": "Could not fetch weather data"}
    except Exception as e:
        logger.error(f"Error in weather endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/time")
async def get_time():
    """Get current time and date"""
    try:
        now = datetime.now()
        return {
            "success": True,
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%A, %B %d, %Y"),
            "datetime": now.strftime("%A, %B %d, %Y at %I:%M %p")
        }
    except Exception as e:
        logger.error(f"Error in time endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """WebSocket endpoint for real-time voice interaction"""
    if not client_id:
        client_id = str(uuid.uuid4())
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "voice_command":
                # Process voice command
                text = message.get("text", "")
                use_context = message.get("use_context", True)
                
                # Process the command
                result = process_voice_command(text, client_id, use_context)
                
                # Send response back to client
                await manager.send_personal_message({
                    "type": "voice_response",
                    "data": result
                }, websocket)
            
            elif message.get("type") == "ping":
                # Respond to ping
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            else:
                # Unknown message type
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Unknown message type"
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_id)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Ashley AI Backend Server starting up...")
    logger.info(f"Assistant Name: {config.get('ASSISTANT_NAME')}")
    logger.info("Server ready to accept connections")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Ashley AI Backend Server shutting down...")
    try:
        tts_cleanup()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
