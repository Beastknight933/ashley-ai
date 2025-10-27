import os
import pickle
import pytz
import threading
import re
import time
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tts import speak as alarm_speak, cleanup as tts_cleanup
from stt import simple_take_command as alarm_take_command, get_microphone_source
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------- CONFIGURATION ----------
SCOPES = ['https://www.googleapis.com/auth/calendar']
ALARM_CHECK_INTERVAL = 30  # Check every 30 seconds
IST = pytz.timezone('Asia/Kolkata')

# ---------- GOOGLE CALENDAR SERVICE ----------
def get_calendar_service():
    """Get or create Google Calendar service with proper error handling."""
    creds = None
    
    try:
        # Load existing credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    logger.error("credentials.json not found!")
                    raise FileNotFoundError("Google credentials file missing")
                
                logger.info("Starting OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                logger.info("Credentials saved")
        
        return build('calendar', 'v3', credentials=creds)
    
    except Exception as e:
        logger.error(f"Failed to get calendar service: {e}")
        raise

# ---------- ALARM CREATION ----------
def create_event(summary, start_time, description='#alarm'):
    """Create a calendar event with proper error handling."""
    try:
        service = get_calendar_service()
        
        # Ensure start_time is timezone-aware
        if start_time.tzinfo is None:
            start_time = IST.localize(start_time)
        
        end_time = start_time + timedelta(minutes=5)
        
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'description': description,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 0}
                ]
            }
        }
        
        result = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Event created: {result.get('htmlLink')}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        return False

# ---------- TIME PARSING ----------
def parse_voice_time(voice_input):
    """
    Parse various voice input formats for alarm time.
    Returns datetime object or None.
    """
    voice_input = voice_input.strip().lower()
    now = datetime.now(IST)
    
    logger.info(f"Parsing time from: {voice_input}")
    
    # Pattern 1: "YYYY-MM-DD HH:MM AM/PM"
    match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})\s*(am|pm)', voice_input, re.IGNORECASE)
    if match:
        date_str = match.group(1)
        hour = int(match.group(2))
        minute = int(match.group(3))
        period = match.group(4).upper()
        
        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
        
        try:
            dt = datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
            return IST.localize(dt)
        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return None
    
    # Pattern 2: "tomorrow at HH:MM AM/PM"
    if "tomorrow" in voice_input:
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', voice_input, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3).upper()
            
            if period == "PM" and hour != 12:
                hour += 12
            elif period == "AM" and hour == 12:
                hour = 0
            
            tomorrow = now + timedelta(days=1)
            alarm_time = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return alarm_time
    
    # Pattern 3: "today at HH:MM AM/PM"
    if "today" in voice_input or "at" in voice_input:
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', voice_input, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3).upper()
            
            if period == "PM" and hour != 12:
                hour += 12
            elif period == "AM" and hour == 12:
                hour = 0
            
            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed, set for tomorrow
            if alarm_time <= now:
                alarm_time += timedelta(days=1)
            
            return alarm_time
    
    # Pattern 4: "in X minutes"
    minutes_match = re.search(r'in\s+(\d+)\s*minutes?', voice_input)
    if minutes_match:
        minutes = int(minutes_match.group(1))
        return now + timedelta(minutes=minutes)
    
    # Pattern 5: "in X hours"
    hours_match = re.search(r'in\s+(\d+)\s*hours?', voice_input)
    if hours_match:
        hours = int(hours_match.group(1))
        return now + timedelta(hours=hours)
    
    # Pattern 6: "HH:MM AM/PM" (today or tomorrow)
    time_only = re.search(r'^(\d{1,2}):(\d{2})\s*(am|pm)$', voice_input, re.IGNORECASE)
    if time_only:
        hour = int(time_only.group(1))
        minute = int(time_only.group(2))
        period = time_only.group(3).upper()
        
        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
        
        alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed, set for tomorrow
        if alarm_time <= now:
            alarm_time += timedelta(days=1)
        
        return alarm_time
    
    logger.warning(f"Could not parse time from: {voice_input}")
    return None

# ---------- ALARM MANAGEMENT ----------
def list_alarms():
    """List all upcoming alarms from Google Calendar."""
    try:
        service = get_calendar_service()
        now = datetime.now(timezone.utc).isoformat()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        alarms = []
        
        for event in events:
            description = event.get('description', '')
            if '#alarm' in description:
                dt_str = event['start'].get('dateTime', event['start'].get('date'))
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                alarms.append({
                    'id': event['id'],
                    'summary': event['summary'],
                    'time': dt,
                    'link': event.get('htmlLink')
                })
        
        if alarms:
            alarm_speak(f"You have {len(alarms)} upcoming alarm{'s' if len(alarms) > 1 else ''}.")
            for i, alarm in enumerate(alarms, 1):
                time_str = alarm['time'].astimezone(IST).strftime("%A, %B %d at %I:%M %p")
                alarm_speak(f"Alarm {i}: {alarm['summary']} on {time_str}")
                logger.info(f"Alarm {i}: {alarm['summary']} - {time_str}")
        else:
            alarm_speak("You have no upcoming alarms.")
        
        return alarms
    
    except Exception as e:
        logger.error(f"Failed to list alarms: {e}")
        alarm_speak("Could not fetch alarms. Please check your connection.")
        return []

def cancel_alarm(alarm_identifier):
    """Cancel a specific alarm by name or number."""
    try:
        service = get_calendar_service()
        now = datetime.now(timezone.utc).isoformat()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        alarms = []
        
        for event in events:
            if '#alarm' in event.get('description', ''):
                alarms.append(event)
        
        # Try to match by number
        if alarm_identifier.isdigit():
            index = int(alarm_identifier) - 1
            if 0 <= index < len(alarms):
                event_to_delete = alarms[index]
                service.events().delete(calendarId='primary', eventId=event_to_delete['id']).execute()
                alarm_speak(f"Alarm '{event_to_delete['summary']}' has been cancelled.")
                logger.info(f"Cancelled alarm: {event_to_delete['summary']}")
                return True
        
        # Try to match by name
        alarm_identifier_lower = alarm_identifier.lower()
        for event in alarms:
            if alarm_identifier_lower in event['summary'].lower():
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                alarm_speak(f"Alarm '{event['summary']}' has been cancelled.")
                logger.info(f"Cancelled alarm: {event['summary']}")
                return True
        
        alarm_speak(f"No alarm found matching '{alarm_identifier}'.")
        return False
    
    except Exception as e:
        logger.error(f"Failed to cancel alarm: {e}")
        alarm_speak("Could not cancel alarm. Please try again.")
        return False

def set_alarm_voice(voice_input, label="Voice Alarm"):
    """Set alarm from voice input with improved parsing."""
    try:
        parsed_time = parse_voice_time(voice_input)
        
        if parsed_time is None:
            alarm_speak("I couldn't understand the time. Try saying 'tomorrow at 10 AM' or 'in 30 minutes'.")
            return False
        
        # Check if time is in the past
        now = datetime.now(IST)
        if parsed_time <= now:
            alarm_speak("That time is in the past. Please specify a future time.")
            return False
        
        # Create the alarm
        if create_event(label, parsed_time):
            time_str = parsed_time.strftime("%A, %B %d at %I:%M %p")
            alarm_speak(f"Alarm '{label}' set for {time_str}")
            logger.info(f"Alarm set: {label} at {time_str}")
            return True
        else:
            alarm_speak("Failed to create alarm. Please try again.")
            return False
    
    except Exception as e:
        logger.error(f"Error setting alarm: {e}")
        alarm_speak("An error occurred while setting the alarm.")
        return False

# ---------- ALARM WATCHER (Background Thread) ----------
def alarm_watcher():
    """Background thread that checks for alarms and triggers them."""
    logger.info("Alarm watcher started")
    
    while True:
        try:
            service = get_calendar_service()
            now = datetime.now(timezone.utc)
            time_min = now.isoformat()
            time_max = (now + timedelta(minutes=1)).isoformat()
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            for event in events:
                if '#alarm' in event.get('description', ''):
                    summary = event['summary']
                    logger.info(f"Alarm triggered: {summary}")
                    alarm_speak(f"ALARM! {summary}")
                    
                    # Optional: Delete the alarm after it triggers
                    # service.events().delete(calendarId='primary', eventId=event['id']).execute()
            
            time.sleep(ALARM_CHECK_INTERVAL)
        
        except Exception as e:
            logger.error(f"Alarm watcher error: {e}")
            time.sleep(ALARM_CHECK_INTERVAL)

# Start the alarm watcher thread
watcher_thread = threading.Thread(target=alarm_watcher, daemon=True)
watcher_thread.start()

# ---------- MAIN EXECUTION ----------
if __name__ == "__main__":
    try:
        print("\n=== ALARM SYSTEM ===")
        print("Commands:")
        print("  - 'set alarm' (then speak or type time)")
        print("  - 'list alarms'")
        print("  - 'cancel alarm' (then specify name or number)")
        print("  - Direct time: 'tomorrow at 10 AM', 'in 30 minutes', etc.")
        print("  - Type time: 'YYYY-MM-DD HH:MM AM/PM'")
        print("  - 'exit' to quit\n")
        
        with get_microphone_source() as source:
            while True:
                try:
                    user_input = input("\nEnter command: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['exit', 'quit', 'stop', 'q']:
                        alarm_speak("Goodbye!")
                        break
                    
                    elif user_input.lower() == 'list alarms':
                        list_alarms()
                    
                    elif user_input.lower().startswith('cancel'):
                        alarm_name = user_input.replace('cancel', '').replace('alarm', '').strip()
                        if alarm_name:
                            cancel_alarm(alarm_name)
                        else:
                            alarm_speak("Which alarm should I cancel? Say the name or number.")
                            alarm_input = input("Alarm to cancel: ").strip()
                            if alarm_input:
                                cancel_alarm(alarm_input)
                    
                    elif user_input.lower() in ['set alarm', 'set', 'alarm']:
                        alarm_speak("What time should I set the alarm for?")
                        time_input = input("Enter time (or press Enter to speak): ").strip()
                        
                        if time_input:
                            label = input("Label (optional, press Enter to skip): ").strip() or "Alarm"
                            set_alarm_voice(time_input, label)
                        else:
                            alarm_speak("Speak the time now.")
                            voice_input = alarm_take_command(source)
                            if voice_input:
                                label = input("Label (optional, press Enter to skip): ").strip() or "Voice Alarm"
                                set_alarm_voice(voice_input, label)
                            else:
                                alarm_speak("Couldn't hear you. Please try again.")
                    
                    else:
                        # Try to parse as direct time input
                        label = input("Label (optional, press Enter to skip): ").strip() or "Quick Alarm"
                        set_alarm_voice(user_input, label)
                
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    logger.error(f"Main loop error: {e}")
                    alarm_speak("An error occurred. Please try again.")
    
    finally:
        tts_cleanup()
        logger.info("Alarm system stopped")