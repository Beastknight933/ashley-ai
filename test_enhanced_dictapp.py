#!/usr/bin/env python3
"""
Test script for enhanced Dictapp.py functionality
"""

from Dictapp import detect_intent, fuzzy_match_app_name, openappweb, closeappweb, list_available_apps

def test_enhanced_app_control():
    """Test the enhanced app control functionality"""
    
    print("=" * 60)
    print("ASHLEY AI - Enhanced App Control Test")
    print("=" * 60)
    
    # Test cases for different types of applications
    test_cases = [
        # Basic applications
        ("open notepad", "open", "notepad", "app"),
        ("launch chrome", "open", "chrome", "app"),
        ("start calculator", "open", "calc", "app"),
        ("run file explorer", "open", "explorer", "app"),
        ("open settings", "open", "ms-settings:", "app"),
        
        # Applications with synonyms
        ("open browser", "open", "chrome", "app"),
        ("launch code editor", "open", "code", "app"),
        ("start terminal", "open", "cmd", "app"),
        ("run word processor", "open", "winword", "app"),
        ("open spreadsheet", "open", "excel", "app"),
        
        # Applications that might be installed
        ("open discord", "open", "discord", "app"),
        ("launch spotify", "open", "spotify", "app"),
        ("start steam", "open", "steam", "app"),
        ("run vlc", "open", "vlc", "app"),
        ("open photoshop", "open", "photoshop", "app"),
        
        # Web URLs
        ("open google.com", "open", "google.com", "web"),
        ("launch youtube.com", "open", "youtube.com", "web"),
        ("start github.com", "open", "github.com", "web"),
        
        # Close commands
        ("close notepad", "close", "notepad", "app"),
        ("kill chrome", "close", "chrome", "app"),
        ("exit calculator", "close", "calc", "app"),
        ("stop discord", "close", "discord", "app"),
    ]
    
    print("\nTesting Intent Detection:")
    print("-" * 40)
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for i, (command, expected_intent, expected_app, expected_type) in enumerate(test_cases, 1):
        intent, app_name, entity_type = detect_intent(command)
        
        # Check if prediction is correct
        intent_correct = intent == expected_intent
        app_correct = app_name == expected_app or (app_name and expected_app in app_name)
        type_correct = entity_type == expected_type
        
        is_correct = intent_correct and app_correct and type_correct
        if is_correct:
            correct_predictions += 1
        
        # Display results
        status = "PASS" if is_correct else "FAIL"
        print(f"{i:2d}. {status} '{command}'")
        print(f"    Expected: {expected_intent} | {expected_app} | {expected_type}")
        print(f"    Got:      {intent} | {app_name} | {entity_type}")
        print()
    
    # Calculate accuracy
    accuracy = (correct_predictions / total_tests) * 100
    print(f"Intent Detection Accuracy: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
    
    # Test fuzzy matching
    print("\n" + "=" * 60)
    print("Testing Fuzzy App Matching:")
    print("-" * 40)
    
    fuzzy_test_cases = [
        ("notepad", "notepad"),
        ("chrome browser", "chrome"),
        ("visual studio code", "code"),
        ("microsoft word", "winword"),
        ("excel spreadsheet", "excel"),
        ("powerpoint presentation", "powerpnt"),
        ("file manager", "explorer"),
        ("system settings", "ms-settings:"),
        ("command prompt", "cmd"),
        ("task manager", "taskmgr"),
        ("paint application", "mspaint"),
        ("calculator app", "calc"),
    ]
    
    fuzzy_correct = 0
    fuzzy_total = len(fuzzy_test_cases)
    
    for query, expected in fuzzy_test_cases:
        result = fuzzy_match_app_name(query)
        is_correct = result == expected
        if is_correct:
            fuzzy_correct += 1
        
        status = "PASS" if is_correct else "FAIL"
        print(f"{status} '{query}' -> {result} (expected: {expected})")
    
    fuzzy_accuracy = (fuzzy_correct / fuzzy_total) * 100
    print(f"\nFuzzy Matching Accuracy: {fuzzy_correct}/{fuzzy_total} ({fuzzy_accuracy:.1f}%)")
    
    # Test app discovery
    print("\n" + "=" * 60)
    print("Testing App Discovery:")
    print("-" * 40)
    
    discovery_tests = [
        "discord",
        "spotify", 
        "steam",
        "vlc",
        "photoshop",
        "notepad++",
        "sublime",
        "atom",
        "pycharm",
    ]
    
    print("Testing if these applications can be found:")
    for app in discovery_tests:
        result = fuzzy_match_app_name(app)
        status = "FOUND" if result else "NOT FOUND"
        print(f"  {status}: {app} -> {result}")
    
    # List available apps
    print("\n" + "=" * 60)
    print("Available Applications:")
    print("-" * 40)
    list_available_apps()
    
    print("\n" + "=" * 60)
    print("Enhanced App Control Test Complete!")
    print("=" * 60)
    
    print("\nKey Improvements:")
    print("+ Expanded app dictionary (50+ applications)")
    print("+ Enhanced synonym support")
    print("+ System-wide app discovery")
    print("+ Better fuzzy matching")
    print("+ Registry-based app detection")
    print("+ Process-based app management")
    print("+ Improved error handling")
    print("+ Graceful fallbacks")

if __name__ == "__main__":
    test_enhanced_app_control()
