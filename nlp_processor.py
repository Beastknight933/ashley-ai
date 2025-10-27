<<<<<<< HEAD
import spacy
from transformers import pipeline
import requests
import json
from rag_system import assistant_rag

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load zero-shot classifier
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define intents
INTENTS = {
    # Basic Interaction
    "greet": ["wake up","good morning", "good evening", "greetings"],
    "exit": ["exit", "quit", "stop", "shutdown", "sleep", "terminate", "goodbye", "end session"],
    
    # AI Identity
    "get_name": ["your name", "who are you", "what is your name", "what do you call yourself"],
    "get_age": ["your age", "how old are you", "what is your age", "when were you created"],
    
    # Small Talk
    "smalltalk_hello": ["hello", "hi","hello there", "hi there", "hey there", "greetings"],
    "smalltalk_howareyou": ["how are you","how r u", "how's it going", "what's up", "how are things"],
    "smalltalk_ok": ["i'm fine", "i am okay", "doing well", "i'm good", "all good"],
    "thanks": ["thank you","thank", "thanks", "appreciate it", "thanks a ton"],
    
    # Search & Info
    "search_google": ["search google for", "look up on google", "google search", "find on google"],
    "search_youtube": ["search youtube for","open youtube for", "look up on youtube", "youtube search", "find on youtube"],
    "search_wikipedia": ["search wikipedia for", "look up on wikipedia", "wikipedia search", "find on wiki"],
    
    # Time & Weather
    "get_time": ["what time is it" , "current time" , "time" , "time now" , "what's the time" , "tell me the time"],
    "get_date": ["what day is it" , "today's date" , "date" , "date now" , "what is the date" , "current date"],
    "temperature": ["temperature" , "what is the temperature here" , "how hot is it" , "how cold is it" , "current temp" , "what's the temp"],
    "weather": ["weather" , "is it raining" , "forecast" , "humidity" , "sunny" , "will it rain"],
    
    # App Control
    "open_app": ["open", "launch", "start app", "run", "open the app", "start the application"],
    "close_app": ["close app", "exit app", "terminate app", "shut app", "kill the app", "stop the application"]
}

def get_intent_spacy(text):
    doc = nlp(text)
    for intent, patterns in INTENTS.items():
        if any(pattern in text for pattern in patterns):
            return intent
    return "unknown"

def get_intent_transformer(text):
    labels = list(INTENTS.keys())
    result = classifier(text, candidate_labels=labels)
    return result["labels"][0] if result["scores"][0] > 0.6 else "unknown"

def fallback_grog(text, api_key):
    response = requests.post(
        "https://api.grog.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": text}]
        }
    )
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()

def fallback_openrouter_gpt5(text, api_key):
    """Fallback function using OpenRouter GPT 5 Pro API with RAG context"""
    try:
        # Retrieve relevant context from knowledge base
        context = assistant_rag.retrieve_context(text)
        
        # Create system message with identity context
        system_message = assistant_rag.get_identity_context()
        
        # Build the prompt with context
        if context:
            enhanced_prompt = f"""Context about me: {system_message}

Relevant information: {context}

User query: {text}

Please respond as Ashley, the AI assistant, using the context provided. Be helpful, professional, and address the user as "sir" when appropriate."""
        else:
            enhanced_prompt = f"""Context about me: {system_message}

User query: {text}

Please respond as Ashley, the AI assistant. Be helpful, professional, and address the user as "sir" when appropriate."""
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ashley-ai.local",  # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "ashley-ai",  # Optional. Site title for rankings on openrouter.ai.
            },
            data=json.dumps({
                "model": "openai/gpt-5-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Ashley, a helpful AI assistant. Use the provided context to maintain your identity and respond appropriately."
                    },
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            })
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return None
=======
import spacy
from transformers import pipeline
import requests
import json
from rag_system import assistant_rag

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load zero-shot classifier
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define intents
INTENTS = {
    # Basic Interaction
    "greet": ["wake up","good morning", "good evening", "greetings"],
    "exit": ["exit", "quit", "stop", "shutdown", "sleep", "terminate", "goodbye", "end session"],
    
    # AI Identity
    "get_name": ["your name", "who are you", "what is your name", "what do you call yourself"],
    "get_age": ["your age", "how old are you", "what is your age", "when were you created"],
    
    # Small Talk
    "smalltalk_hello": ["hello", "hi","hello there", "hi there", "hey there", "greetings"],
    "smalltalk_howareyou": ["how are you","how r u", "how's it going", "what's up", "how are things"],
    "smalltalk_ok": ["i'm fine", "i am okay", "doing well", "i'm good", "all good"],
    "thanks": ["thank you","thank", "thanks", "appreciate it", "thanks a ton"],
    
    # Search & Info
    "search_google": ["search google for", "look up on google", "google search", "find on google"],
    "search_youtube": ["search youtube for","open youtube for", "look up on youtube", "youtube search", "find on youtube"],
    "search_wikipedia": ["search wikipedia for", "look up on wikipedia", "wikipedia search", "find on wiki"],
    
    # Time & Weather
    "get_time": ["what time is it" , "current time" , "time" , "time now" , "what's the time" , "tell me the time"],
    "get_date": ["what day is it" , "today's date" , "date" , "date now" , "what is the date" , "current date"],
    "temperature": ["temperature" , "what is the temperature here" , "how hot is it" , "how cold is it" , "current temp" , "what's the temp"],
    "weather": ["weather" , "is it raining" , "forecast" , "humidity" , "sunny" , "will it rain"],
    
    # App Control
    "open_app": ["open", "launch", "start app", "run", "open the app", "start the application"],
    "close_app": ["close app", "exit app", "terminate app", "shut app", "kill the app", "stop the application"]
}

def get_intent_spacy(text):
    doc = nlp(text)
    for intent, patterns in INTENTS.items():
        if any(pattern in text for pattern in patterns):
            return intent
    return "unknown"

def get_intent_transformer(text):
    labels = list(INTENTS.keys())
    result = classifier(text, candidate_labels=labels)
    return result["labels"][0] if result["scores"][0] > 0.6 else "unknown"

def fallback_grog(text, api_key):
    response = requests.post(
        "https://api.grog.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": text}]
        }
    )
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()

def fallback_openrouter_gpt5(text, api_key):
    """Fallback function using OpenRouter GPT 5 Pro API with RAG context"""
    try:
        # Retrieve relevant context from knowledge base
        context = assistant_rag.retrieve_context(text)
        
        # Create system message with identity context
        system_message = assistant_rag.get_identity_context()
        
        # Build the prompt with context
        if context:
            enhanced_prompt = f"""Context about me: {system_message}

Relevant information: {context}

User query: {text}

Please respond as Ashley, the AI assistant, using the context provided. Be helpful, professional, and address the user as "sir" when appropriate."""
        else:
            enhanced_prompt = f"""Context about me: {system_message}

User query: {text}

Please respond as Ashley, the AI assistant. Be helpful, professional, and address the user as "sir" when appropriate."""
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ashley-ai.local",  # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "ashley-ai",  # Optional. Site title for rankings on openrouter.ai.
            },
            data=json.dumps({
                "model": "openai/gpt-5-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Ashley, a helpful AI assistant. Use the provided context to maintain your identity and respond appropriately."
                    },
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            })
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return None
>>>>>>> e9ec500827f6070334915ca072792ad71474e6c7
