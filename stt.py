import speech_recognition as sr

# Initialize recognizer once
recognizer = sr.Recognizer()

def take_command(source, timeout=8, phrase_time_limit=3, language='en-US'):
    """
    Convert speech to text using Google Speech Recognition.
    
    Args:
        source: Microphone source object
        timeout (int): Timeout in seconds to wait for speech to start (default: 8)
        phrase_time_limit (int): Maximum time to listen for a phrase (default: 3)
        language (str): Language code for recognition (default: 'en-US')
    
    Returns:
        str: Recognized text or empty string if no speech detected/error occurred
    """
    print("Listening...")

    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.5  # Adjusts silence allowed between words
    recognizer.energy_threshold = 300  # You can auto-calibrate if needed

    frames = []
    sample_rate = 16000  # Default fallback value
    sample_width = 2     # Default fallback (16-bit audio)

    try:
        # Wait for the user to start speaking
        audio = recognizer.listen(source, timeout=timeout)
        frames.append(audio.get_raw_data())
        sample_rate = audio.sample_rate
        sample_width = audio.sample_width

        # Continue listening as long as the user is speaking
        print("Capturing speech...")
        while True:
            # Non-blocking listen with short timeout
            next_audio = recognizer.listen(source, timeout=1, phrase_time_limit=phrase_time_limit)
            frames.append(next_audio.get_raw_data())

    except sr.WaitTimeoutError:
        if not frames:
            message = "no speech detected. skipping response."
            print(message)
            return ""

    except sr.UnknownValueError:
        message = "Sorry, I didn't catch that."
        print(message)
        return ""

    except sr.RequestError as e:
        message = f"Could not request results; {e}"
        print(message)
        return ""

    except Exception:
        # Likely finished speaking or silence reached
        pass

    # Combine frames into one AudioData object
    combined_audio = sr.AudioData(b"".join(frames), sample_rate, sample_width)

    try:
        print("Recognizing...")
        query = recognizer.recognize_google(combined_audio, language=language)
        print(f"You said: {query}\n")
        return query

    except sr.UnknownValueError:
        message = "Sorry, I couldn't understand what you said."
    except sr.RequestError as e:
        message = f"Could not request results; {e}"
    except Exception as e:
        message = f"An error occurred: {e}"

    print(message)
    return ""

def simple_take_command(source, timeout=8, language='en-US'):
    """
    Simplified speech-to-text function (from alarm.py).
    Good for basic voice input without continuous listening.
    
    Args:
        source: Microphone source object
        timeout (int): Timeout in seconds to wait for speech (default: 8)
        language (str): Language code for recognition (default: 'en-US')
    
    Returns:
        str: Recognized text or empty string if no speech detected/error occurred
    """
    try:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source, timeout=timeout)
        query = recognizer.recognize_google(audio, language=language)
        print(f"You said: {query}")
        return query
    except sr.WaitTimeoutError:
        return ""
    except Exception as e:
        print(f"Speech recognition error: {e}")
        return ""

def calibrate_microphone(source, duration=1):
    """
    Calibrate microphone for ambient noise.
    
    Args:
        source: Microphone source object
        duration (int): Duration in seconds for calibration (default: 1)
    """
    print("Calibrating microphone... Please stay quiet.")
    recognizer.adjust_for_ambient_noise(source, duration=duration)
    print("Calibration complete. You may speak now.\n")

def get_microphone_source():
    """
    Get a microphone source object.
    
    Returns:
        Microphone source object
    """
    return sr.Microphone()
