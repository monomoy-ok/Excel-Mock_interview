# app/main.py

from app.interview_graph import build_interview_graph
from app.utils import print_with_typing, log_event, translate_text, get_lang_code
from app.voice_utils import speak
import os
import pickle
SESSION_FILE = "data/session.pkl"
from app.config import LOGO_TEXT, PRIMARY_COLOR, INTRO_TEXT

try:
    from colorama import Fore, Style
except ImportError:
    Fore = Style = None

def save_session(state):
    with open(SESSION_FILE, "wb") as f:
        pickle.dump(state, f)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "rb") as f:
            return pickle.load(f)
    return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def display_welcome():
    print_with_typing("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                        Coding Ninjas AI Interview                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
📣 AI says: Welcome to Coding Ninjas AI Interview System!

   This AI-powered interview will assess your Excel knowledge and generate a detailed report.

    Take your time and speak naturally.
    """, color=Fore.CYAN if Fore else None)
    speak("Welcome to Coding Ninjas AI Interview System! This AI-powered interview will assess your Excel knowledge and generate a detailed report. Take your time and speak naturally.", language='en')

def display_privacy_notice(language='english'):
    # Empty function as privacy notice is now handled in nodes.py
    pass

def select_language():
    languages = ["English", "Hindi", "Spanish", "French"]
    print_with_typing("Please select your preferred language:", color=Fore.YELLOW if Fore else None)
    for idx, lang in enumerate(languages, 1):
        print_with_typing(f"{idx}. {lang}")
    speak("Please select your preferred language. Say the number or the language name.")
    from app.voice_utils import listen
    response = listen(timeout=10, phrase_time_limit=5).strip().lower()
    selected = "english"
    for idx, lang in enumerate(languages, 1):
        if str(idx) in response or lang.lower() in response:
            selected = lang.lower()
            break
    print_with_typing(f"Language selected: {selected.title()}", color=Fore.GREEN if Fore else None)
    speak(f"You have selected {selected.title()}.")
    return selected

def offer_data_deletion(final_state):
    print_with_typing("Would you like to request deletion of your data and report? (yes/no)", color=Fore.YELLOW if Fore else None)
    speak("Would you like to request deletion of your data and report? Please say yes or no.")
    from app.voice_utils import listen
    response = listen(timeout=10, phrase_time_limit=5).strip().lower()
    if "yes" in response or "y" in response:
        # Delete session file
        clear_session()
        # Delete report file if exists
        report_path = final_state.get("report")
        if report_path and os.path.exists(report_path):
            os.remove(report_path)
        print_with_typing("Your data and report have been deleted.", color=Fore.GREEN if Fore else None)
        speak("Your data and report have been deleted.")
    else:
        print_with_typing("Your data and report are retained.", color=Fore.GREEN if Fore else None)
        speak("Your data and report are retained.")

def auto_save_worker(state, interval=60):
    """Background worker for auto-saving the interview state."""
    import time
    while True:
        time.sleep(interval)
        if state.get('needs_save'):
            save_session(state)
            state['needs_save'] = False
            log_event("Auto-saved interview state")

def run_interview():
    log_event("Interview session started.")
    display_welcome()
    language = 'english'
    display_privacy_notice(language)
    
    # Initialize state
    state = {"language": language, "needs_save": False}
    
    # Session recovery
    if os.path.exists(SESSION_FILE):
        print_with_typing("A previous interview session was found. Would you like to resume? (yes/no)", color=Fore.YELLOW if Fore else None)
        speak("A previous interview session was found. Would you like to resume? Please say yes or no.", language='en')
        from app.voice_utils import listen
        response = listen(timeout=10, phrase_time_limit=5, language='en-US').strip().lower()
        if "yes" in response or "y" in response:
            state = load_session()
            print_with_typing("Resuming previous session...", color=Fore.GREEN if Fore else None)
            speak("Resuming previous session.", language='en')
        else:
            clear_session()
    
    # Start auto-save in background
    import threading
    auto_save_thread = threading.Thread(target=auto_save_worker, args=(state,), daemon=True)
    auto_save_thread.start()
    if os.path.exists(SESSION_FILE):
        print_with_typing("A previous interview session was found. Would you like to resume? (yes/no)", color=Fore.YELLOW if Fore else None)
        speak("A previous interview session was found. Would you like to resume? Please say yes or no.", language='en')
        from app.voice_utils import listen
        response = listen(timeout=10, phrase_time_limit=5, language='en-US').strip().lower()
        if "yes" in response or "y" in response:
            state = load_session()
            print_with_typing("Resuming previous session...", color=Fore.GREEN if Fore else None)
            speak("Resuming previous session.", language='en')
        else:
            clear_session()
    interview_graph = build_interview_graph()
    # Start the graph with the loaded or empty state
    if state is None:
        state = {"language": language}
    else:
        state["language"] = language
    final_state = interview_graph.invoke(state)
    save_session(final_state)
    clear_session()
    if final_state.get("complete"):
        print_with_typing("\u2705 Interview complete. Report successfully generated.", color=Fore.GREEN if Fore else None)
        if final_state.get("report"):
            print_with_typing(f"\U0001F4C4 Report saved at: {final_state['report']}", color=Fore.CYAN if Fore else None)
        log_event("Interview session completed successfully.")

if __name__ == "__main__":
    run_interview()
