import datetime
from nlp_processor import get_intent_spacy, get_intent_transformer, fallback_grog
from weather_utils import handle_temperature, handle_weather
from tts import speak, cleanup as tts_cleanup
from stt import take_command, calibrate_microphone, get_microphone_source


# ---------- MAIN AI ASSISTANT LOOP ----------
def assistant_loop():
    with get_microphone_source() as source:
        calibrate_microphone(source)

        while True:
            query = take_command(source).lower().strip()
            if not query:
                continue

            # Primary intent detection
            intent = get_intent_transformer(query)
            if intent == "unknown":
                intent = get_intent_spacy(query)

            # Dynamic dispatch using intent
            if intent == "greet":
                try:
                    from GreetMe import greetMe
                    greetMe()
                except ImportError as e:
                    speak("GreetMe module not found.")
                    print(f"Import error: {e}")
                except Exception as e:
                    speak("An error occurred while greeting.")
                    print(f"GreetMe error: {e}")

            elif intent == "exit":
                speak("Alright, have a great day! I'm just a call away.")
                break

            elif intent == "get_name":
                speak("My name is Ashley, your AI assistant.")

            elif intent == "smalltalk_hello":
                speak("Hello! How are you?")

            elif intent == "smalltalk_ok":
                speak("That's great to hear, sir.")

            elif intent == "smalltalk_howareyou":
                speak("Perfectly fine sir, thank you for asking.")

            elif intent == "thanks":
                speak("You're welcome, sir.")

            elif intent == "get_age":
                speak("I am a computer program, so I don't have an age.")

            elif intent == "search_google":
                from SearchNow import search_google
                search_google(query)

            elif intent == "search_youtube":
                from SearchNow import search_youtube
                search_youtube(query)

            elif intent == "search_wikipedia":
                from SearchNow import search_wikipedia
                search_wikipedia(query)

            elif intent == "temperature":
                handle_temperature(query)

            elif intent == "weather":
                handle_weather(query)

            elif intent == "get_time":
                now = datetime.datetime.now()
                strTime = now.strftime("%I:%M %p")
                speak(f"Sir, the time is {strTime}")

            elif intent == "get_date":
                now = datetime.datetime.now()
                strDate = now.strftime("%A, %B %d, %Y")
                speak(f"Today is {strDate}")

            elif intent == "open_app":
                from Dictapp import openappweb
                openappweb(query)

            elif intent == "close_app":
                from Dictapp import closeappweb
                closeappweb(query)

            else:
                           # Fallback using Grog AI
                response = fallback_grog(query, "YOUR_GROG_API_KEY")
                if response:
                        print(f"Grog AI response: {response}")
                        speak(response)
                else:
                        print("Grog AI did not return a valid response.")
                        speak("I couldn't find an answer to that.")

# ---------- CLEANUP ----------
def cleanup():
    tts_cleanup()

# ---------- RUN ----------
if __name__ == "__main__":
    try:
        assistant_loop()
    finally:
        cleanup()



