import os
import pickle
import datetime
import speech_recognition as sr
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from alarm import speak1, take_command, create_event

SCOPES = ['https://www.googleapis.com/auth/tasks']
recognizer = sr.Recognizer()

def get_tasks_service():
    creds = None
    if os.path.exists('token-tasks.pickle'):
        with open('token-tasks.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            preferred_port_env = os.getenv('GOOGLE_OAUTH_PORT')
            preferred_port = int(preferred_port_env) if preferred_port_env else 51018
            try:
                creds = flow.run_local_server(
                    port=preferred_port,
                    open_browser=True,
                    authorization_prompt_message='Please visit this URL to authorize: {url}',
                    success_message='Authorization complete. You may close this window.'
                )
            except OSError as e:
                # If binding fails (port in use or blocked), fall back to manual console flow
                creds = flow.run_console(authorization_prompt_message='Please visit this URL to authorize: {url}')
        with open('token-tasks.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('tasks', 'v1', credentials=creds)

def get_input_method():
    speak1("Would you like to type the task or say it out loud?")
    choice = input("Type 'voice' or 'text': ").strip().lower()
    if 'voice' in choice:
        with sr.Microphone() as source:
            speak1("Listening for your task...")
            task_name = take_command(source)
    else:
        task_name = input("Enter task name: ")
    return task_name

def ask_for_due_date():
    speak1("Do you want to add a deadline to this task? Say yes or no.")
    with sr.Microphone() as source:
        answer = take_command(source).lower()
    if 'yes' in answer:
        speak1("Please say or type the due date in format YYYY-MM-DD")
        try:
            due_input = input("Due Date: ")
            datetime.datetime.strptime(due_input, "%Y-%m-%d")  # Validate format
            return due_input
        except ValueError:
            speak1("Invalid date format. Skipping deadline.")
    return None

def create_task():
    service = get_tasks_service()
    task_name = get_input_method()
    if not task_name:
        speak1("Task name was empty. Try again later.")
        return

    due_date = ask_for_due_date()
    task = {'title': task_name}
    if due_date:
        iso_due = due_date + 'T00:00:00.000Z'
        task['due'] = iso_due

        # Create corresponding alarm event
        alarm_dt = datetime.datetime.strptime(due_date, "%Y-%m-%d")
        create_event(task_name, alarm_dt)
        speak1("Linked calendar alarm has been created.")

    service.tasks().insert(tasklist='@default', body=task).execute()
    speak1(f"Task '{task_name}' has been added.")

if __name__ == '__main__':
    create_task()

