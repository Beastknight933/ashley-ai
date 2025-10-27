import requests
import re
from tts import speak, cleanup

def get_location():
    try:
        res = requests.get("http://ip-api.com/json/")
        data = res.json()
        city = data.get("city", "Kolkata")
        return city
    except Exception as e:
        print(f"Location fetch error: {e}")
        return "Kolkata"

def extract_city_from_query(query):
    match = re.search(r'\b(?:in|at)\s+([A-Za-z\s]+)', query)
    if match:
        return match.group(1).strip().title()
    return None

def get_openweather_data(city):
    api_key = "b65eb9ee0fca7de0e11c36c6b6f76fa6"  # Replace with your real API key
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        res = requests.get(url)
        data = res.json()
        if data.get("cod") != 200:
            print("Weather API error:", data.get("message"))
            return None
        return {
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "description": data["weather"][0]["description"].capitalize(),
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"]
        }
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return None

def speak_temperature(data, city):
    temp = data["temperature"]
    feels_like = data["feels_like"]
    speak(f"The current temperature in {city} is {temp} degrees Celsius. It feels like {feels_like} degrees.")

def speak_weather(data, city):
    desc = data["description"]
    humidity = data["humidity"]
    wind_speed = data["wind_speed"]
    speak(f"The weather in {city} is currently {desc}, with humidity at {humidity} percent and wind speed at {wind_speed} meters per second.")

def handle_temperature(query):
    city = extract_city_from_query(query)
    if not city:
        city = get_location()
    data = get_openweather_data(city)
    if data:
        speak_temperature(data, city)
    else:
        speak("Sorry, I couldn't fetch the temperature right now.")

def handle_weather(query):
    city = extract_city_from_query(query)
    if not city:
        city = get_location()
    data = get_openweather_data(city)
    if data:
        speak_weather(data, city)
    else:
        speak("Sorry, I couldn't fetch the weather information right now.")

def cleanup_weather():
    cleanup()

# For testing standalone
if __name__ == "__main__":
    try:
        handle_weather("What's the weather in Delhi?")
        handle_temperature("What's the temperature in Delhi?")
    finally:
        cleanup_weather()
