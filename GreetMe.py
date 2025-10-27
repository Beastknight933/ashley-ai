import datetime
from tts import speak_with_temp_dir as speak, cleanup

def greetMe():
    hour = int(datetime.datetime.now().hour)

    if 0 <= hour <= 12:
        speak("Good Morning,sir. welcome back")
    elif 12 < hour <= 18:
        speak("Good Afternoon,sir. welcome back")
    else:
        speak("Good Evening,sir. welcome back")

    speak("how can I help you today?")

def cleanup_greet():
    cleanup()

if __name__ == "__main__":
    try:
        greetMe()
    finally:
        cleanup_greet()

