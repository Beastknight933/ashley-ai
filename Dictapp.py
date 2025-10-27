import pyautogui
import webbrowser
import re
import shutil
import difflib
import os
import subprocess
import winreg
import psutil
from time import sleep
from pathlib import Path
from tts import speak, cleanup

# Try to load spaCy NLP model, fallback if not available
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (OSError, ImportError):
    print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None
    SPACY_AVAILABLE = False

# Enhanced application dictionary with more apps
basic_app_dict = {
    # Microsoft Office
    "word": "winword",
    "excel": "excel", 
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "onenote": "onenote",
    "access": "msaccess",
    "publisher": "mspub",
    
    # Browsers
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "safari": "safari",
    "opera": "opera",
    
    # Development Tools
    "vscode": "code",
    "visual studio": "devenv",
    "notepad": "notepad",
    "notepad++": "notepad++",
    "sublime": "sublime_text",
    "atom": "atom",
    "pycharm": "pycharm64",
    "intellij": "idea64",
    "eclipse": "eclipse",
    "android studio": "studio64",
    
    # System Tools
    "commandprompt": "cmd",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings": "ms-settings:",
    "file explorer": "explorer",
    "calculator": "calc",
    "paint": "mspaint",
    "snipping tool": "snippingtool",
    "character map": "charmap",
    "disk cleanup": "cleanmgr",
    "device manager": "devmgmt.msc",
    "event viewer": "eventvwr",
    "services": "services.msc",
    "registry editor": "regedit",
    "system information": "msinfo32",
    
    # Media & Graphics
    "photos": "ms-photos:",
    "media player": "wmplayer",
    "vlc": "vlc",
    "photoshop": "photoshop",
    "gimp": "gimp",
    "paint.net": "paintdotnet",
    "blender": "blender",
    "sketchup": "sketchup",
    
    # Communication
    "teams": "ms-teams",
    "zoom": "zoom",
    "skype": "skype",
    "discord": "discord",
    "slack": "slack",
    "telegram": "telegram",
    "whatsapp": "whatsapp",
    
    # Utilities
    "winrar": "winrar",
    "7zip": "7zFM",
    "adobe reader": "acrord32",
    "spotify": "spotify",
    "steam": "steam",
    "epic games": "epicgameslauncher",
    "origin": "origin",
    "uplay": "uplay",
    
    # Cloud & Storage
    "onedrive": "onedrive",
    "dropbox": "dropbox",
    "google drive": "googledrivesync",
    "icloud": "icloud",
}

# Enhanced synonym dictionary
synonym_dict = {
    # Document editors
    "document editor": "word",
    "text editor": "notepad",
    "word processor": "word",
    "documents": "word",
    
    # Spreadsheets
    "spreadsheet": "excel",
    "spreadsheets": "excel",
    "excel file": "excel",
    
    # Presentations
    "presentation": "powerpoint",
    "slides": "powerpoint",
    "ppt": "powerpoint",
    
    # Browsers
    "browser": "chrome",
    "web browser": "chrome",
    "internet": "chrome",
    "web": "chrome",
    
    # Code editors
    "code editor": "vscode",
    "editor": "vscode",
    "ide": "vscode",
    "programming": "vscode",
    "coding": "vscode",
    
    # Terminal/Command line
    "terminal": "commandprompt",
    "command line": "commandprompt",
    "cmd": "commandprompt",
    "shell": "powershell",
    
    # System utilities
    "files": "file explorer",
    "explorer": "file explorer",
    "my computer": "file explorer",
    "this pc": "file explorer",
    "computer": "file explorer",
    "system": "settings",
    "preferences": "settings",
    "config": "settings",
    
    # Media
    "music": "spotify",
    "video": "vlc",
    "movies": "vlc",
    "image editor": "photoshop",
    "photo editor": "photoshop",
    "pictures": "photos",
    "images": "photos",
    
    # Communication
    "chat": "discord",
    "messaging": "discord",
    "video call": "zoom",
    "meeting": "teams",
    "conference": "teams",
    
    # Games
    "games": "steam",
    "gaming": "steam",
    "game": "steam",
}

# Common executable patterns
executable_patterns = [
    r"(\w+)\.exe$",
    r"(\w+)\.bat$",
    r"(\w+)\.cmd$",
    r"(\w+)\.com$",
]

# Context memory
context = {
    "last_action": None,
    "last_app": None,
    "last_type": None,  # "app" or "web"
    "discovered_apps": set(),  # Cache for discovered apps
}

def get_installed_apps():
    """Get list of installed applications from Windows registry"""
    installed_apps = set()
    
    try:
        # Check both 32-bit and 64-bit registry locations
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        
        for hkey, subkey in registry_paths:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey_handle:
                                try:
                                    display_name = winreg.QueryValueEx(subkey_handle, "DisplayName")[0]
                                    installed_apps.add(display_name.lower())
                                except FileNotFoundError:
                                    pass
                        except OSError:
                            continue
            except FileNotFoundError:
                continue
                
    except Exception as e:
        print(f"Warning: Could not read registry: {e}")
    
    return installed_apps

def get_running_processes():
    """Get list of currently running processes"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['name']:
                    processes.append(proc.info['name'].lower().replace('.exe', ''))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    except Exception as e:
        print(f"Warning: Could not get running processes: {e}")
        return []

def search_executable_in_paths(app_name):
    """Search for executable in common system paths"""
    search_paths = [
        os.environ.get('PATH', '').split(os.pathsep),
        [r'C:\Program Files'],
        [r'C:\Program Files (x86)'],
        [r'C:\Users\{}\AppData\Local'.format(os.getenv('USERNAME', ''))],
        [r'C:\Users\{}\AppData\Roaming'.format(os.getenv('USERNAME', ''))],
        [r'C:\Windows\System32'],
        [r'C:\Windows'],
    ]
    
    # Flatten the list
    all_paths = []
    for path_list in search_paths:
        all_paths.extend(path_list)
    
    # Search for executables
    for path in all_paths:
        if not os.path.exists(path):
            continue
            
        try:
            for root, dirs, files in os.walk(path):
                # Limit depth to avoid long searches
                if root.count(os.sep) - path.count(os.sep) > 3:
                    dirs.clear()
                    continue
                    
                for file in files:
                    if file.lower().startswith(app_name.lower()) and file.lower().endswith(('.exe', '.bat', '.cmd', '.com')):
                        full_path = os.path.join(root, file)
                        if os.access(full_path, os.X_OK):
                            return full_path
        except (PermissionError, OSError):
            continue
    
    return None

def fuzzy_match_app_name(query):
    """Enhanced fuzzy matching for application names"""
    query_lower = query.lower().strip()
    
    # Direct match in basic dictionary
    if query_lower in basic_app_dict:
        return basic_app_dict[query_lower]
    
    # Direct match in synonym dictionary
    if query_lower in synonym_dict:
        return basic_app_dict.get(synonym_dict[query_lower], synonym_dict[query_lower])
    
    # Fuzzy matching against all known apps
    all_apps = list(basic_app_dict.keys()) + list(synonym_dict.keys())
    matches = difflib.get_close_matches(query_lower, all_apps, n=3, cutoff=0.6)
    
    if matches:
        best_match = matches[0]
        if best_match in synonym_dict:
            return basic_app_dict.get(synonym_dict[best_match], synonym_dict[best_match])
        elif best_match in basic_app_dict:
            return basic_app_dict[best_match]
    
    # Try to find executable directly
    if shutil.which(query_lower):
        return query_lower
    
    # Search for executable in system paths
    executable_path = search_executable_in_paths(query_lower)
    if executable_path:
        return os.path.basename(executable_path).replace('.exe', '')
    
    return None

def detect_intent(query):
    """Enhanced intent detection with better app name extraction"""
    if SPACY_AVAILABLE and nlp:
        doc = nlp(query.lower())
        intent = None
        app_name = None
        
        # Detect intent
        for token in doc:
            if token.lemma_ in ["open", "launch", "start", "run", "execute"]:
                intent = "open"
            elif token.lemma_ in ["close", "kill", "terminate", "exit", "stop", "quit"]:
                intent = "close"
        
        # Extract app name using NLP
        app_keywords = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop:
                app_keywords.append(token.text)
        
        if app_keywords:
            app_name = " ".join(app_keywords)
    else:
        # Fallback without spaCy
        intent = None
        app_name = None
        
        # Simple keyword detection
        open_words = ["open", "launch", "start", "run", "execute"]
        close_words = ["close", "kill", "terminate", "exit", "stop", "quit"]
        
        query_lower = query.lower()
        for word in open_words:
            if word in query_lower:
                intent = "open"
                break
        
        if not intent:
            for word in close_words:
                if word in query_lower:
                    intent = "close"
                    break
        
        # Extract potential app name (everything after intent word)
        if intent:
            words = query_lower.split()
            intent_word_idx = -1
            for i, word in enumerate(words):
                if word in open_words + close_words:
                    intent_word_idx = i
                    break
            
            if intent_word_idx >= 0 and intent_word_idx < len(words) - 1:
                app_name = " ".join(words[intent_word_idx + 1:])
    
    # Check for web URL
    url_match = re.search(r"(?:\bwww\.|\b)([\w-]+(?:\.[\w]+)+)", query)
    if url_match:
        app_name = url_match.group(1)
        return intent, app_name, "web"
    
    # Try to match app name
    if app_name:
        matched_app = fuzzy_match_app_name(app_name)
        if matched_app:
            return intent, matched_app, "app"
    
    return intent, None, None

def openappweb(query=None):
    """Enhanced app opening function"""
    if not query:
        speak("No command provided.")
        return False
    
    intent, app_name, entity_type = detect_intent(query)
    if intent != "open" or not app_name:
        speak("Sorry, I couldn't figure out what to open.")
        return False
    
    speak("Launching, sir")
    context.update({"last_action": "open", "last_app": app_name, "last_type": entity_type})
    
    try:
        if entity_type == "web":
            # Handle web URLs
            if not app_name.startswith("http"):
                app_name = f"https://www.{app_name}"
            webbrowser.open(app_name)
            speak(f"Opening {app_name} in your browser")
            return True
        
        elif entity_type == "app":
            # Handle applications
            success = False
            
            # Try direct execution first
            if shutil.which(app_name):
                subprocess.Popen([app_name], shell=True)
                speak(f"Opening {app_name}")
                success = True
            else:
                # Try with .exe extension
                exe_name = f"{app_name}.exe"
                if shutil.which(exe_name):
                    subprocess.Popen([exe_name], shell=True)
                    speak(f"Opening {app_name}")
                    success = True
                else:
                    # Try Windows start command
                    try:
                        subprocess.run(f"start {app_name}", shell=True, check=True)
                        speak(f"Opening {app_name}")
                        success = True
                    except subprocess.CalledProcessError:
                        # Try with quotes for names with spaces
                        try:
                            subprocess.run(f'start "{app_name}"', shell=True, check=True)
                            speak(f"Opening {app_name}")
                            success = True
                        except subprocess.CalledProcessError:
                            pass
            
            if not success:
                speak(f"Sorry, I couldn't find or open {app_name}. It might not be installed or accessible.")
                return False
            
            return True
    
    except Exception as e:
        print(f"Error opening {app_name}: {e}")
        speak(f"Sorry, there was an error opening {app_name}")
        return False

def closeappweb(query=None):
    """Enhanced app closing function"""
    if not query:
        speak("No command provided.")
        return False
    
    intent, app_name, entity_type = detect_intent(query)
    
    # Use context if no app name
    if not app_name:
        app_name = context.get("last_app")
        entity_type = context.get("last_type")
    
    if intent != "close" or not app_name:
        speak("Sorry, I couldn't figure out what to close.")
        return False
    
    speak("Closing, sir")
    context.update({"last_action": "close", "last_app": app_name, "last_type": entity_type})
    
    try:
        if "tab" in query.lower():
            # Handle browser tab closing
            match = re.search(r"(\d+)\s*tab", query)
            count = int(match.group(1)) if match else 1
            for _ in range(count):
                pyautogui.hotkey("ctrl", "w")
                sleep(0.5)
            speak("Tab closed" if count == 1 else f"{count} tabs closed")
            return True
        
        elif entity_type == "web":
            # Close browser tab
            pyautogui.hotkey("ctrl", "w")
            speak("Web tab closed")
            return True
        
        elif entity_type == "app":
            # Close application
            success = False
            
            # Try to find and kill the process
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
                            proc.terminate()
                            speak(f"Closing {app_name}")
                            success = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if not success:
                    # Try with taskkill command
                    exe_name = f"{app_name}.exe"
                    subprocess.run(f"taskkill /f /im {exe_name}", shell=True, check=True)
                    speak(f"Closing {app_name}")
                    success = True
                    
            except subprocess.CalledProcessError:
                speak(f"Sorry, I couldn't close {app_name}. It might not be running.")
                return False
            
            return success
    
    except Exception as e:
        print(f"Error closing {app_name}: {e}")
        speak(f"Sorry, there was an error closing {app_name}")
        return False

def list_available_apps():
    """List available applications that can be opened"""
    print("Available applications:")
    print("-" * 40)
    
    # List basic apps
    print("Basic Applications:")
    for name, exe in basic_app_dict.items():
        print(f"  • {name} -> {exe}")
    
    print("\nSynonyms:")
    for synonym, app in synonym_dict.items():
        print(f"  • {synonym} -> {app}")
    
    # List some discovered apps
    if context["discovered_apps"]:
        print("\nRecently Discovered:")
        for app in list(context["discovered_apps"])[:10]:  # Show first 10
            print(f"  • {app}")

def cleanup_dictapp():
    """Cleanup function"""
    cleanup()

# Test function
def test_app_control():
    """Test the enhanced app control functionality"""
    print("Testing Enhanced App Control")
    print("=" * 40)
    
    test_commands = [
        "open notepad",
        "open chrome",
        "open file explorer",
        "open calculator",
        "open settings",
        "open discord",
        "open spotify",
        "close notepad",
        "close chrome",
    ]
    
    for cmd in test_commands:
        print(f"\nTesting: '{cmd}'")
        intent, app_name, entity_type = detect_intent(cmd)
        print(f"  Intent: {intent}")
        print(f"  App: {app_name}")
        print(f"  Type: {entity_type}")

if __name__ == "__main__":
    # Test the enhanced functionality
    test_app_control()
    print("\n" + "=" * 40)
    list_available_apps()