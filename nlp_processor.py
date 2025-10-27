import spacy
from transformers import pipeline
import requests
import json
import re
import difflib
from typing import Dict, List, Tuple, Optional
from rag_system import assistant_rag

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

# Load zero-shot classifier
try:
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception as e:
    print(f"Warning: Could not load transformer model: {e}")
    classifier = None

# Enhanced intent patterns with more variety and context awareness
INTENTS = {
    # Basic Interaction
    "greet": [
        "wake up", "wake", "awaken", "activate", "hey ashley", "hey assistant",
        "good morning", "good afternoon", "good evening", "good day",
        "greetings", "hello", "hi", "hey", "hiya", "howdy", "sup",
        "hello there", "hi there", "hey there", "good to see you",
        "rise and shine", "time to wake up", "are you there", "are you awake"
    ],
    
    "exit": [
        "exit", "quit", "stop", "shutdown", "sleep", "terminate", "end",
        "goodbye", "bye", "see you later", "talk to you later", "catch you later",
        "end session", "close session", "shut down", "power off", "turn off",
        "that's all", "that's it", "nothing else", "i'm done", "all done",
        "thanks that's all", "no more questions", "sign off", "log off"
    ],
    
    # AI Identity & Capabilities
    "get_name": [
        "your name", "who are you", "what is your name", "what do you call yourself",
        "what should i call you", "what's your name", "introduce yourself",
        "tell me about yourself", "who am i talking to", "what's your identity",
        "are you ashley", "is your name ashley", "do you have a name"
    ],
    
    "get_age": [
        "your age", "how old are you", "what is your age", "when were you created",
        "when were you born", "how long have you existed", "what's your age",
        "are you old", "are you young", "how long have you been around"
    ],
    
    "get_capabilities": [
        "what can you do", "what are your capabilities", "what do you help with",
        "what services do you provide", "what functions do you have",
        "what are you good at", "what can you help me with", "your abilities",
        "your skills", "what do you offer", "your features", "your functions"
    ],
    
    # Small Talk & Social
    "smalltalk_hello": [
        "hello", "hi", "hey", "hiya", "howdy", "sup", "yo", "greetings",
        "hello there", "hi there", "hey there", "good to see you",
        "nice to meet you", "pleasure to meet you", "how do you do"
    ],
    
    "smalltalk_howareyou": [
        "how are you", "how r u", "how's it going", "what's up", "how are things",
        "how do you feel", "are you okay", "how are you doing", "how's life",
        "how's everything", "how's your day", "how are you feeling",
        "are you well", "how's it hanging", "what's new", "how's work"
    ],
    
    "smalltalk_ok": [
        "i'm fine", "i am okay", "doing well", "i'm good", "all good",
        "great", "excellent", "wonderful", "fantastic", "amazing",
        "not bad", "pretty good", "so so", "could be better", "i'm alright"
    ],
    
    "smalltalk_weather": [
        "nice weather", "beautiful day", "lovely weather", "terrible weather",
        "awful weather", "weather is great", "weather is bad", "it's hot",
        "it's cold", "it's warm", "it's cool", "perfect weather"
    ],
    
    "thanks": [
        "thank you", "thank", "thanks", "appreciate it", "thanks a ton",
        "much appreciated", "thanks a lot", "thank you very much", "grateful",
        "thanks so much", "thanks a bunch", "many thanks", "cheers",
        "thanks for that", "thanks for helping", "thanks for the help"
    ],
    
    "compliment": [
        "you're great", "you're amazing", "you're wonderful", "you're awesome",
        "you're fantastic", "you're brilliant", "you're smart", "you're helpful",
        "good job", "well done", "excellent work", "great work", "nice work",
        "you rock", "you're the best", "you're perfect", "you're incredible"
    ],
    
    # Search & Information
    "search_google": [
        "search google for", "look up on google", "google search", "find on google",
        "search for", "look up", "find information about", "google it",
        "search the web for", "web search", "internet search", "browse for",
        "can you search", "please search", "i need to search", "help me search"
    ],
    
    "search_youtube": [
        "search youtube for", "open youtube for", "look up on youtube", 
        "youtube search", "find on youtube", "search youtube", "youtube it",
        "find videos about", "look for videos", "search for videos",
        "youtube videos", "video search", "watch videos about"
    ],
    
    "search_wikipedia": [
        "search wikipedia for", "look up on wikipedia", "wikipedia search", 
        "find on wiki", "wikipedia it", "search wiki", "look up in wikipedia",
        "find information on wikipedia", "wikipedia article", "wiki search",
        "encyclopedia search", "reference search"
    ],
    
    "general_search": [
        "search for", "find", "look up", "search", "find information",
        "look for", "seek", "hunt for", "track down", "discover"
    ],
    
    # Time & Date
    "get_time": [
        "what time is it", "current time", "time", "time now", "what's the time",
        "tell me the time", "what time", "time please", "current time please",
        "what's the current time", "time check", "what time is it now",
        "can you tell me the time", "time update", "what's the clock say"
    ],
    
    "get_date": [
        "what day is it", "today's date", "date", "date now", "what is the date",
        "current date", "what's today", "what day is today", "today's day",
        "what's the date today", "date please", "current date please",
        "what's today's date", "day and date", "what's the calendar say"
    ],
    
    "get_datetime": [
        "what's the date and time", "date and time", "full date and time",
        "complete date time", "date time now", "current date and time",
        "what's the full date and time", "date time please"
    ],
    
    # Weather & Temperature
    "temperature": [
        "temperature", "what is the temperature", "how hot is it", "how cold is it",
        "current temp", "what's the temp", "temperature here", "temp now",
        "how's the temperature", "what's the temperature like", "temp check",
        "temperature reading", "how hot", "how cold", "degrees", "celsius",
        "fahrenheit", "is it hot", "is it cold", "temperature outside"
    ],
    
    "weather": [
        "weather", "is it raining", "forecast", "humidity", "sunny", "will it rain",
        "weather today", "weather now", "current weather", "weather conditions",
        "weather report", "weather update", "how's the weather", "weather check",
        "is it sunny", "is it cloudy", "is it windy", "weather outside",
        "weather forecast", "will it be sunny", "will it rain today"
    ],
    
    "weather_extended": [
        "weather in", "temperature in", "forecast for", "weather at",
        "how's the weather in", "what's the weather like in", "weather conditions in",
        "temperature in", "forecast in", "weather report for"
    ],
    
    # Application Control
    "open_app": [
        "open", "launch", "start app", "run", "open the app", "start the application",
        "open application", "launch application", "start program", "run program",
        "open program", "execute", "begin", "initiate", "activate",
        "open up", "fire up", "boot up", "start up", "turn on"
    ],
    
    "close_app": [
        "close app", "exit app", "terminate app", "shut app", "kill the app",
        "stop the application", "close application", "exit application",
        "quit app", "end app", "shut down app", "close program",
        "exit program", "terminate program", "stop program", "kill program",
        "shut down", "turn off", "close down", "end", "quit"
    ],
    
    "app_control": [
        "switch to", "change to", "go to", "navigate to", "focus on",
        "bring up", "show", "display", "minimize", "maximize", "restore"
    ],
    
    # Alarm & Reminder Management
    "set_alarm": [
        "set an alarm", "set alarm", "create alarm", "add alarm", "new alarm",
        "remind me", "set reminder", "create reminder", "schedule alarm",
        "alarm for", "reminder for", "wake me up", "alert me", "notify me",
        "set timer", "countdown", "schedule", "book", "plan"
    ],
    
    "list_alarms": [
        "list alarms", "show alarms", "my alarms", "alarm list", "reminders",
        "what alarms", "show reminders", "alarm schedule", "upcoming alarms",
        "scheduled alarms", "my reminders", "alarm list", "reminder list"
    ],
    
    "cancel_alarm": [
        "cancel alarm", "delete alarm", "remove alarm", "stop alarm",
        "cancel reminder", "delete reminder", "remove reminder", "stop reminder",
        "turn off alarm", "disable alarm", "clear alarm", "erase alarm"
    ],
    
    # System Control
    "volume_up": [
        "volume up", "louder", "increase volume", "turn up volume", "make it louder",
        "volume higher", "boost volume", "crank it up", "pump up the volume"
    ],
    
    "volume_down": [
        "volume down", "quieter", "decrease volume", "turn down volume", "make it quieter",
        "volume lower", "reduce volume", "turn it down", "lower the volume"
    ],
    
    "repeat": [
        "repeat", "say again", "say that again", "repeat that", "once more",
        "again please", "can you repeat", "repeat please", "say it again",
        "one more time", "repeat the last", "repeat yourself"
    ],
    
    "help": [
        "help", "what can you do", "how do you work", "instructions", "guide",
        "tutorial", "how to use", "user manual", "commands", "available commands",
        "what commands", "how can you help", "assistance", "support"
    ],
    
    # Conversational
    "question": [
        "what", "how", "why", "when", "where", "who", "which", "can you",
        "do you know", "tell me about", "explain", "describe", "define",
        "what is", "how does", "why is", "when is", "where is", "who is"
    ],
    
    "confirmation": [
        "yes", "yeah", "yep", "sure", "okay", "ok", "alright", "right",
        "correct", "that's right", "exactly", "absolutely", "definitely",
        "of course", "certainly", "indeed", "affirmative", "roger"
    ],
    
    "negation": [
        "no", "nope", "nah", "not", "don't", "won't", "can't", "shouldn't",
        "wouldn't", "couldn't", "never", "nothing", "none", "neither",
        "negative", "incorrect", "wrong", "false", "disagree"
    ]
}

# Context patterns for better intent detection
CONTEXT_PATTERNS = {
    "location": [
        "in", "at", "near", "around", "here", "there", "this place", "this location"
    ],
    "time_reference": [
        "now", "today", "tomorrow", "yesterday", "this week", "next week",
        "this month", "next month", "this year", "next year", "tonight",
        "this morning", "this afternoon", "this evening", "later", "soon"
    ],
    "urgency": [
        "urgent", "asap", "immediately", "right now", "quickly", "fast",
        "emergency", "important", "priority", "critical", "rush"
    ]
}

def preprocess_text(text: str) -> str:
    """Preprocess text for better intent recognition"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower().strip()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove punctuation at the end
    text = re.sub(r'[.!?]+$', '', text)
    
    # Expand contractions
    contractions = {
        "i'm": "i am", "you're": "you are", "he's": "he is", "she's": "she is",
        "it's": "it is", "we're": "we are", "they're": "they are",
        "don't": "do not", "doesn't": "does not", "didn't": "did not",
        "won't": "will not", "can't": "cannot", "couldn't": "could not",
        "shouldn't": "should not", "wouldn't": "would not", "haven't": "have not",
        "hasn't": "has not", "hadn't": "had not", "isn't": "is not",
        "aren't": "are not", "wasn't": "was not", "weren't": "were not"
    }
    
    for contraction, expansion in contractions.items():
        text = text.replace(contraction, expansion)
    
    return text

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract entities from text using spaCy"""
    entities = {
        "location": [],
        "time": [],
        "app_name": [],
        "search_query": [],
        "alarm_time": []
    }
    
    if not nlp:
        return entities
    
    doc = nlp(text)
    
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:  # Geopolitical entity or location
            entities["location"].append(ent.text)
        elif ent.label_ in ["TIME", "DATE"]:  # Time or date
            entities["time"].append(ent.text)
        elif ent.label_ == "PERSON":  # Person names (could be app names)
            entities["app_name"].append(ent.text)
    
    # Extract search queries (text after search keywords)
    search_keywords = ["search", "find", "look up", "google", "youtube", "wikipedia"]
    for keyword in search_keywords:
        if keyword in text:
            # Extract text after the keyword
            pattern = rf"{keyword}\s+(?:for\s+)?(.+)"
            match = re.search(pattern, text)
            if match:
                entities["search_query"].append(match.group(1).strip())
    
    # Extract alarm times
    alarm_patterns = [
        r"at\s+(\d{1,2}:\d{2})",  # "at 10:30"
        r"(\d{1,2}:\d{2})",  # "10:30"
        r"(\d{1,2})\s*(am|pm)",  # "10 am"
        r"(\d{1,2})\s*(a\.m\.|p\.m\.)",  # "10 a.m."
    ]
    
    for pattern in alarm_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                entities["alarm_time"].append(" ".join(match))
            else:
                entities["alarm_time"].append(match)
    
    return entities

def calculate_similarity_score(text: str, patterns: List[str]) -> float:
    """Calculate similarity score between text and patterns"""
    if not text or not patterns:
        return 0.0
    
    text_words = set(text.lower().split())
    max_score = 0.0
    
    for pattern in patterns:
        pattern_words = set(pattern.lower().split())
        
        # Calculate Jaccard similarity
        intersection = text_words.intersection(pattern_words)
        union = text_words.union(pattern_words)
        
        if union:
            jaccard_score = len(intersection) / len(union)
            
            # Bonus for exact substring match
            if pattern.lower() in text.lower():
                jaccard_score += 0.3
            
            # Bonus for fuzzy match
            fuzzy_score = difflib.SequenceMatcher(None, text.lower(), pattern.lower()).ratio()
            if fuzzy_score > 0.7:
                jaccard_score += fuzzy_score * 0.2
            
            max_score = max(max_score, jaccard_score)
    
    return max_score

def get_intent_spacy(text: str) -> str:
    """Enhanced spaCy-based intent classification"""
    if not nlp:
        return "unknown"
    
    text = preprocess_text(text)
    if not text:
        return "unknown"
    
    doc = nlp(text)
    
    # Calculate scores for all intents
    intent_scores = {}
    
    for intent, patterns in INTENTS.items():
        # Direct pattern matching
        pattern_score = calculate_similarity_score(text, patterns)
        
        # Linguistic analysis
        linguistic_score = 0.0
        
        # Check for key verbs and nouns
        for token in doc:
            if token.pos_ in ["VERB", "NOUN", "ADJ"]:
                token_text = token.lemma_.lower()
                for pattern in patterns:
                    if token_text in pattern.lower():
                        linguistic_score += 0.1
        
        # Combine scores
        total_score = pattern_score + linguistic_score
        intent_scores[intent] = total_score
    
    # Return the intent with the highest score
    if intent_scores:
        best_intent = max(intent_scores, key=intent_scores.get)
        if intent_scores[best_intent] > 0.3:  # Threshold for confidence
            return best_intent
    
    return "unknown"

def get_intent_transformer(text: str) -> Tuple[str, float]:
    """Enhanced transformer-based intent classification"""
    if not classifier:
        return "unknown", 0.0
    
    text = preprocess_text(text)
    if not text:
        return "unknown", 0.0
    
    labels = list(INTENTS.keys())
    result = classifier(text, candidate_labels=labels)
    
    best_intent = result["labels"][0]
    confidence = result["scores"][0]
    
    return best_intent, confidence

def get_intent_hybrid(text: str) -> Tuple[str, float, Dict]:
    """Hybrid intent classification combining multiple methods"""
    text = preprocess_text(text)
    if not text:
        return "unknown", 0.0, {}
    
    # Get results from both methods
    spacy_intent = get_intent_spacy_simple(text)
    transformer_intent, transformer_confidence = get_intent_transformer(text)
    
    # Extract entities
    entities = extract_entities(text)
    
    # Determine final intent
    if spacy_intent == transformer_intent and spacy_intent != "unknown":
        # Both methods agree
        final_intent = spacy_intent
        confidence = max(0.8, transformer_confidence)
    elif transformer_confidence > 0.7:
        # Transformer is very confident
        final_intent = transformer_intent
        confidence = transformer_confidence
    elif spacy_intent != "unknown":
        # spaCy found something
        final_intent = spacy_intent
        confidence = 0.6
    else:
        # Neither method is confident
        final_intent = "unknown"
        confidence = 0.0
    
    return final_intent, confidence, entities

def get_intent_with_context(text: str, conversation_history: List[str] = None) -> Tuple[str, float, Dict]:
    """Get intent with conversation context"""
    intent, confidence, entities = get_intent_hybrid(text)
    
    # Add context from conversation history
    if conversation_history and len(conversation_history) > 0:
        # Look for follow-up patterns
        if intent == "unknown":
            last_intent = get_intent_hybrid(conversation_history[-1])[0]
            
            # Common follow-up patterns
            follow_up_patterns = {
                "search_google": ["more about", "tell me more", "additional info", "more details"],
                "weather": ["in another city", "different location", "somewhere else"],
                "set_alarm": ["for tomorrow", "next week", "different time"],
                "open_app": ["another app", "different program", "something else"]
            }
            
            if last_intent in follow_up_patterns:
                for pattern in follow_up_patterns[last_intent]:
                    if pattern in text.lower():
                        intent = last_intent
                        confidence = 0.7
                        break
    
    return intent, confidence, entities

def fallback_grog(text: str, api_key: str) -> str:
    """Fallback function using Grog API"""
    try:
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
    except Exception as e:
        print(f"Grog API error: {e}")
        return None

def fallback_openrouter_gpt5(text: str, api_key: str) -> str:
    """Enhanced fallback function using OpenRouter GPT 5 Pro API with RAG context"""
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
                "HTTP-Referer": "https://ashley-ai.local",
                "X-Title": "ashley-ai",
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

# Backward compatibility functions
def get_intent_spacy_simple(text: str) -> str:
    """Simple spaCy-based intent classification without hybrid approach"""
    if not nlp:
        return "unknown"
    
    text = preprocess_text(text)
    if not text:
        return "unknown"
    
    doc = nlp(text)
    
    # Calculate scores for all intents
    intent_scores = {}
    
    for intent, patterns in INTENTS.items():
        # Direct pattern matching
        pattern_score = calculate_similarity_score(text, patterns)
        
        # Linguistic analysis
        linguistic_score = 0.0
        
        # Check for key verbs and nouns
        for token in doc:
            if token.pos_ in ["VERB", "NOUN", "ADJ"]:
                token_text = token.lemma_.lower()
                for pattern in patterns:
                    if token_text in pattern.lower():
                        linguistic_score += 0.1
        
        # Combine scores
        total_score = pattern_score + linguistic_score
        intent_scores[intent] = total_score
    
    # Return the intent with the highest score
    if intent_scores:
        best_intent = max(intent_scores, key=intent_scores.get)
        if intent_scores[best_intent] > 0.3:  # Threshold for confidence
            return best_intent
    
    return "unknown"

def get_intent_transformer_simple(text: str) -> str:
    """Simple transformer-based intent classification"""
    if not classifier:
        return "unknown"
    
    text = preprocess_text(text)
    if not text:
        return "unknown"
    
    labels = list(INTENTS.keys())
    result = classifier(text, candidate_labels=labels)
    
    best_intent = result["labels"][0]
    confidence = result["scores"][0]
    
    return best_intent if confidence > 0.6 else "unknown"