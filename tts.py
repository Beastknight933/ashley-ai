import subprocess
import pygame
import os
import uuid
import glob
import time
import tempfile

# Initialize pygame mixer once
pygame.init()
pygame.mixer.init()

def speak(audio, voice="en-US-MichelleNeural", use_ssml=False):
    """
    Convert text to speech using edge-tts and play it with pygame.
    Automatically cleans up the temporary MP3 file after playback.
    
    Args:
        audio (str): Text to convert to speech
        voice (str): Voice to use for TTS (default: "en-US-MichelleNeural")
        use_ssml (bool): Whether to wrap text in SSML for special effects (default: False)
    """
    output_file = f"output_{uuid.uuid4()}.mp3"

    # Wrap text in SSML if requested (useful for Medusa voice effects)
    text_to_speak = audio
    if use_ssml:
        text_to_speak = f"""
        <speak version="1.0" xml:lang="en-US">
          <voice name="{voice}">
            <prosody rate="slow" pitch="-3st">
              {audio}
            </prosody>
          </voice>
        </speak>
        """

    try:
        subprocess.run(
            ["edge-tts", "--voice", voice, "--text", text_to_speak, "--write-media", output_file],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print("Error generating speech:")
        print(e.stderr)
        # Clean up the file even if TTS generation failed
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as cleanup_error:
                print(f"Failed to cleanup failed TTS file: {cleanup_error}")
        return

    try:
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

    except Exception as e:
        print(f"Playback error: {e}")
    
    finally:
        # Always clean up the temporary file after playback (or error)
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
                print(f"Cleaned up: {output_file}")
            except Exception as cleanup_error:
                print(f"Failed to cleanup TTS file {output_file}: {cleanup_error}")

def speak_with_temp_dir(audio, voice="en-US-MichelleNeural"):
    """
    Alternative TTS implementation using temporary directory (from GreetMe.py).
    Useful when you need better file cleanup.
    
    Args:
        audio (str): Text to convert to speech
        voice (str): Voice to use for TTS (default: "en-US-MichelleNeural")
    """
    # Use a temporary directory
    temp_dir = tempfile.gettempdir()
    filename = f"output_{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(temp_dir, filename)

    try:
        result = subprocess.run(
            ["edge-tts", "--voice", voice, "--text", audio, "--write-media", output_path],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print("TTS generation failed:", e.stderr)
        return

    try:
        pygame.mixer.music.load(output_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"Playback error: {e}")

    finally:
        pygame.mixer.music.stop()

        # Try unloading (for pygame 2.1+)
        try:
            pygame.mixer.music.unload()
        except:  # noqa: E722
            pass

        # Wait to ensure file is released
        time.sleep(0.3)

        # Try to delete the file
        try:
            os.remove(output_path)
            print(f"Deleted: {output_path}")
        except Exception as e:
            print(f"Failed to delete {output_path}: {e}")

def cleanup():
    """
    Emergency cleanup function to remove any leftover MP3 files.
    Note: The main speak() function now cleans up files automatically.
    """
    try:
        # Extra safety: delete any leftover mp3s from crashes or interruptions
        for file in glob.glob("output_*.mp3"):
            try:
                os.remove(file)
                print(f"Emergency cleanup removed: {file}")
            except Exception as e:
                print(f"Emergency cleanup failed for {file}: {e}")

        pygame.mixer.quit()
    except Exception as e:
        print(f"Error during emergency cleanup: {e}")

# Convenience function for Medusa voice (with SSML effects)
def medusa_speak(audio):
    """
    Speak with Medusa voice effects (slower, deeper tone).
    """
    speak(audio, voice="en-GB-LibbyNeural", use_ssml=True)

# Convenience function for standard Ashley voice
def ashley_speak(audio):
    """
    Speak with standard Ashley voice.
    """
    speak(audio, voice="en-US-MichelleNeural", use_ssml=False)
