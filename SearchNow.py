import webbrowser
import wikipedia
from tts import speak, cleanup


# ---------- SEARCH FUNCTIONS ----------

def search_google(query):
    speak(f"Searching {query}")
    webbrowser.open(f"https://www.google.com/search?q={query}")

def search_youtube(query):
    speak(f"Searching {query}")
    webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

def search_wikipedia(query):
    speak(f"Searching {query}")

    try:
        # Normalize and clean the query
        query = query.lower().strip()
        if "search wikipedia for" in query:
            search_term = query.replace("search wikipedia for", "").strip()
        elif "search wikipedia on" in query:
            search_term = query.replace("search wikipedia on", "").strip()
        else:
            search_term = query

        # Get Wikipedia page and open in browser
        page = wikipedia.page(search_term)
        webbrowser.open(page.url)
    except wikipedia.exceptions.DisambiguationError:
        speak("There are multiple possible results. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak("No Wikipedia page found for that query.")
    except Exception as e:
        speak("An error occurred while opening Wikipedia.")
        print(f"Wikipedia error: {e}")

# ---------- CLEANUP ----------

def cleanup_search():
    cleanup()

# ---------- USAGE EXAMPLE ----------

if __name__ == "__main__":
    try:
        search_google("Python programming")
        search_youtube("Python tutorials")
        search_wikipedia("Artificial Intelligence")
    finally:
        cleanup_search()

    
