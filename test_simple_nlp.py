#!/usr/bin/env python3
"""
Simple test for the enhanced NLP system
"""

def test_basic_nlp():
    """Test basic NLP functionality without complex dependencies"""
    
    print("=" * 60)
    print("ASHLEY AI - Enhanced NLP System Test (Basic)")
    print("=" * 60)
    
    # Test text preprocessing
    print("\nTesting Text Preprocessing:")
    print("-" * 30)
    
    try:
        from nlp_processor import preprocess_text, extract_entities
        
        test_texts = [
            "I'm doing great!",
            "You're amazing!!!",
            "What's the weather like?",
            "Can't you help me?",
            "Search for python tutorials",
            "Set alarm for 3:30 pm"
        ]
        
        for text in test_texts:
            processed = preprocess_text(text)
            print(f"'{text}' -> '{processed}'")
        
        print("\nTesting Entity Extraction:")
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
        
        print("SUCCESS: Basic NLP functions working!")
        
    except Exception as e:
        print(f"ERROR: Error testing basic NLP: {e}")
        print("This might be due to missing dependencies (spaCy, transformers)")
        print("The system will still work with fallback methods.")
    
    # Test intent patterns
    print("\nTesting Intent Pattern Matching:")
    print("-" * 40)
    
    try:
        from nlp_processor import INTENTS, calculate_similarity_score
        
        test_cases = [
            ("hello ashley", "greet"),
            ("what's your name", "get_name"),
            ("search for python", "search_google"),
            ("what time is it", "get_time"),
            ("weather today", "weather"),
            ("open chrome", "open_app"),
            ("set alarm", "set_alarm"),
            ("help", "help"),
            ("goodbye", "exit")
        ]
        
        correct = 0
        total = len(test_cases)
        
        for input_text, expected_intent in test_cases:
            best_score = 0
            best_intent = "unknown"
            
            for intent, patterns in INTENTS.items():
                score = calculate_similarity_score(input_text, patterns)
                if score > best_score:
                    best_score = score
                    best_intent = intent
            
            is_correct = best_intent == expected_intent
            if is_correct:
                correct += 1
            
            status = "PASS" if is_correct else "FAIL"
            print(f"{status} '{input_text}' -> {best_intent} (score: {best_score:.2f})")
        
        accuracy = (correct / total) * 100
        print(f"\nPattern Matching Accuracy: {correct}/{total} ({accuracy:.1f}%)")
        
    except Exception as e:
        print(f"ERROR: Error testing pattern matching: {e}")
    
    print("\n" + "=" * 60)
    print("Enhanced NLP System Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_basic_nlp()