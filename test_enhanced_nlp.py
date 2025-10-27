#!/usr/bin/env python3
"""
Test script for the enhanced NLP system
"""

from nlp_processor import get_intent_hybrid, get_intent_with_context, preprocess_text, extract_entities

def test_nlp_enhancements():
    """Test the enhanced NLP system with various inputs"""
    
    print("=" * 60)
    print("ASHLEY AI - Enhanced NLP System Test")
    print("=" * 60)
    
    # Test cases with expected intents
    test_cases = [
        # Greetings
        ("hello ashley", "greet"),
        ("hey there", "smalltalk_hello"),
        ("good morning", "greet"),
        ("wake up", "greet"),
        
        # Identity questions
        ("what's your name", "get_name"),
        ("who are you", "get_name"),
        ("what can you do", "get_capabilities"),
        ("your abilities", "get_capabilities"),
        
        # Small talk
        ("how are you", "smalltalk_howareyou"),
        ("what's up", "smalltalk_howareyou"),
        ("i'm doing great", "smalltalk_ok"),
        ("thank you", "thanks"),
        ("you're amazing", "compliment"),
        
        # Search
        ("search for python tutorials", "search_google"),
        ("google machine learning", "search_google"),
        ("find videos about cooking", "search_youtube"),
        ("wikipedia artificial intelligence", "search_wikipedia"),
        
        # Time and date
        ("what time is it", "get_time"),
        ("current time", "get_time"),
        ("what's today's date", "get_date"),
        ("date and time", "get_datetime"),
        
        # Weather
        ("what's the temperature", "temperature"),
        ("how hot is it", "temperature"),
        ("weather today", "weather"),
        ("is it raining", "weather"),
        ("weather in new york", "weather_extended"),
        
        # App control
        ("open chrome", "open_app"),
        ("launch vscode", "open_app"),
        ("close word", "close_app"),
        ("exit excel", "close_app"),
        
        # Alarms
        ("set an alarm", "set_alarm"),
        ("remind me at 3pm", "set_alarm"),
        ("list my alarms", "list_alarms"),
        ("cancel alarm", "cancel_alarm"),
        
        # System
        ("help", "help"),
        ("repeat that", "repeat"),
        ("volume up", "volume_up"),
        ("louder", "volume_up"),
        
        # Exit
        ("goodbye", "exit"),
        ("see you later", "exit"),
        ("that's all", "exit"),
    ]
    
    print("\nTesting Enhanced Intent Classification:")
    print("-" * 50)
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for i, (input_text, expected_intent) in enumerate(test_cases, 1):
        # Get intent with hybrid method
        intent, confidence, entities = get_intent_hybrid(input_text)
        
        # Check if prediction is correct
        is_correct = intent == expected_intent
        if is_correct:
            correct_predictions += 1
        
        # Display results
        status = "✓" if is_correct else "✗"
        print(f"{i:2d}. {status} '{input_text}'")
        print(f"    Expected: {expected_intent}")
        print(f"    Got: {intent} (confidence: {confidence:.2f})")
        if entities:
            print(f"    Entities: {entities}")
        print()
    
    # Calculate accuracy
    accuracy = (correct_predictions / total_tests) * 100
    print(f"Accuracy: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
    
    # Test context awareness
    print("\n" + "=" * 60)
    print("Testing Context Awareness:")
    print("-" * 30)
    
    conversation_history = [
        "search for python tutorials",
        "tell me more about that",
        "what about machine learning"
    ]
    
    context_tests = [
        ("more about that", "search_google"),  # Should follow from search
        ("in another city", "weather_extended"),  # Should follow from weather
        ("different time", "set_alarm"),  # Should follow from alarm
    ]
    
    for input_text, expected_intent in context_tests:
        intent, confidence, entities = get_intent_with_context(input_text, conversation_history)
        print(f"'{input_text}' -> {intent} (confidence: {confidence:.2f})")
    
    # Test entity extraction
    print("\n" + "=" * 60)
    print("Testing Entity Extraction:")
    print("-" * 30)
    
    entity_tests = [
        "search for python programming in new york",
        "weather in london tomorrow",
        "set alarm for 3:30 pm",
        "open chrome browser",
    ]
    
    for text in entity_tests:
        entities = extract_entities(text)
        print(f"'{text}'")
        print(f"  Entities: {entities}")
        print()
    
    # Test text preprocessing
    print("=" * 60)
    print("Testing Text Preprocessing:")
    print("-" * 30)
    
    preprocessing_tests = [
        "I'm doing great!",
        "You're amazing!!!",
        "What's the weather like?",
        "Can't you help me?",
    ]
    
    for text in preprocessing_tests:
        processed = preprocess_text(text)
        print(f"'{text}' -> '{processed}'")
    
    print("\n" + "=" * 60)
    print("Enhanced NLP System Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_nlp_enhancements()
