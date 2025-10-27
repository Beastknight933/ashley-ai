import pyautogui
import webbrowser
import re
import shutil
import difflib
import spacy
from time import sleep
from tts import speak, cleanup

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Core application dictionary
basic_app_dict = {
    "commandprompt": "cmd",
    "paint": "paint",
    "word": "winword",
    "excel": "excel",
    "chrome": "chrome",
    "vscode": "code",
    "powerpoint": "powerpnt"
}

synonym_dict = {
    "document editor": "word",
    "spreadsheet": "excel",
    "browser": "chrome",
    "code editor": "vscode",
    "presentation": "powerpoint",
    "terminal": "commandprompt"
}

# Context memory
context = {
    "last_action": None,
    "last_app": None,
    "last_type": None  # "app" or "web"
}


def fuzzy_match_app_name(query):
    words = query.lower().split()
    possible_apps = list(basic_app_dict.keys()) + list(synonym_dict.keys())
    match = difflib.get_close_matches(" ".join(words), possible_apps, n=1, cutoff=0.5)
    if match:
        matched_key = match[0]
        return synonym_dict.get(matched_key, matched_key)
    return None

def detect_intent(query):
    doc = nlp(query.lower())
    intent = None
    app_name = None

    for token in doc:
        if token.lemma_ in ["open", "launch", "start", "run"]:
            intent = "open"
        elif token.lemma_ in ["close", "kill", "terminate", "exit", "stop"]:
            intent = "close"

    # Try to extract application name or web domain
    url_match = re.search(r"(?:\bwww\.|\b)([\w-]+(?:\.[\w]+)+)", query)
    if url_match:
        app_name = url_match.group(1)
        return intent, app_name, "web"

    app_name = fuzzy_match_app_name(query)
    if not app_name:
        # Try by executable name
        for token in doc:
            if shutil.which(token.text):
                app_name = token.text
                break

    if app_name:
        return intent, app_name, "app"
    
    return intent, None, None

def openappweb(query=None):
    if not query:
        speak("No command provided.")
        return

    intent, app_name, entity_type = detect_intent(query)
    if intent != "open" or not app_name:
        speak("Sorry, I couldn't figure out what to open.")
        return

    speak("Launching, sir")
    context.update({"last_action": "open", "last_app": app_name, "last_type": entity_type})

    if entity_type == "web":
        if not app_name.startswith("http"):
            app_name = f"https://www.{app_name}"
        webbrowser.open(app_name)
        return

    if app_name in basic_app_dict:
        os.system(f"start {basic_app_dict[app_name]}")
        return

    if shutil.which(app_name):
        os.system(f"start {app_name}")
        return

    speak("Sorry, I couldn't find that application.")

def closeappweb(query=None):
    if not query:
        speak("No command provided.")
        return

    intent, app_name, entity_type = detect_intent(query)

    # Use context if no app name
    if not app_name:
        app_name = context.get("last_app")
        entity_type = context.get("last_type")

    if intent != "close" or not app_name:
        speak("Sorry, I couldn't figure out what to close.")
        return

    speak("Closing, sir")
    context.update({"last_action": "close", "last_app": app_name, "last_type": entity_type})

    if "tab" in query:
        match = re.search(r"(\d+)\s*tab", query)
        count = int(match.group(1)) if match else 1
        for _ in range(count):
            pyautogui.hotkey("ctrl", "w")
            sleep(0.5)
        speak("Tab closed" if count == 1 else "All tabs closed")
        return

    if entity_type == "app":
        exe_name = basic_app_dict.get(app_name, app_name)
        os.system(f"taskkill /f /im {exe_name}.exe")
    else:
        pyautogui.hotkey("ctrl", "w")
        speak("Web tab closed")

def cleanup_dictapp():
    cleanup()
