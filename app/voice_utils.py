# app/voice_utils.py

import pyttsx3
import speech_recognition as sr
import threading
from app.config import VOICE_RATE, VOICE_VOLUME, VOICE_PITCH
from gtts import gTTS
import tempfile
from playsound import playsound
from app.utils import print_with_typing
try:
    from colorama import Fore, Style
except ImportError:
    Fore = Style = None


def speak(text: str, language='en'):
    """Speak out the given text using pyttsx3 for English, gTTS for other languages."""
    print(f"\U0001F4E3 AI says: {text}")
    if language.startswith('en'):
        engine = pyttsx3.init(driverName='sapi5')
        voices = engine.getProperty('voices')
        # Prefer Zira (female), then David (male), else first available
        selected_voice = None
        for v in voices:
            if 'zira' in v.name.lower():
                selected_voice = v.id
                break
        if not selected_voice:
            for v in voices:
                if 'david' in v.name.lower():
                    selected_voice = v.id
                    break
        if not selected_voice and voices:
            selected_voice = voices[0].id
        if selected_voice:
            engine.setProperty('voice', selected_voice)
        engine.setProperty('rate', VOICE_RATE)
        engine.setProperty('volume', VOICE_VOLUME)
        try:
            engine.setProperty('pitch', VOICE_PITCH)
        except Exception:
            pass
        engine.say(text)
        engine.runAndWait()
    else:
        speak_gtts(text, language)

def speak_gtts(text, language):
    """Speak text using gTTS for the given language code (e.g., 'hi' for Hindi). Uses pygame for playback on all platforms."""
    import platform
    try:
        print(f"[TTS] Using gTTS with language code: {language}")
        tts = gTTS(text=text, lang=language.split('-')[0])
        import os
        import pygame
        fp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(fp.name)
        fp.close()
        pygame.mixer.init()
        pygame.mixer.music.load(fp.name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
        pygame.mixer.quit()
        os.remove(fp.name)
    except Exception as e:
        print(f"[TTS error: {e}] (text: {text}, lang: {language})")
        print("[TTS] Could not speak the phrase. Please check your internet connection and gTTS installation.")

def listen(timeout=8, phrase_time_limit=15, language='en-US', max_retries=3, is_followup=False):
    """
    Capture voice input with improved error handling and retries.
    
    For follow-up questions, uses a shorter timeout to move on more quickly if no response.
    """
    recognizer = sr.Recognizer()
    # Increase recognition sensitivity
    recognizer.energy_threshold = 300  # Default is 300, lower is more sensitive
    recognizer.dynamic_energy_threshold = True
    
    # Use shorter timeout for follow-up questions
    if is_followup:
        timeout = min(timeout, 3)  # Max 3 seconds for follow-ups
        max_retries = 1  # Only retry once for follow-ups
        
    retries = 0
    
    while retries <= max_retries:
        with sr.Microphone() as source:
            print_with_typing("\U0001F3A4 Listening..." + (" (Retry)" if retries > 0 else ""),
                            color=Fore.GREEN if Fore else None)
            # Increase ambient noise adjustment duration
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                response = recognizer.recognize_google(audio, language=language)
                print_with_typing(f"You said: {response}", color=Fore.GREEN if Fore else None)
                return response
            except sr.WaitTimeoutError:
                if retries < max_retries:
                    error_msg = "I didn't catch that. Could you speak a bit louder or move closer to the microphone?"
                    print_with_typing(f"❌ {error_msg}",
                                    color=Fore.YELLOW if Fore else None)
                    speak(error_msg)
                    retries += 1
                    continue
                else:
                    error_msg = "I didn't hear anything. Let's try typing instead:"
                    print_with_typing(error_msg,
                                    color=Fore.YELLOW if Fore else None)
                    speak(error_msg)
                    return input("Your response: ")
            except sr.UnknownValueError:
                if retries < max_retries:
                    error_msg = "I'm having trouble understanding. Could you speak a bit more clearly?"
                    print_with_typing(f"❌ {error_msg}",
                                    color=Fore.YELLOW if Fore else None)
                    speak(error_msg)
                    retries += 1
                    continue
                else:
                    error_msg = "I'm  having trouble understanding. Let's try typing instead:"
                    print_with_typing(error_msg,
                                    color=Fore.YELLOW if Fore else None)
                    speak(error_msg)
                    return input("Your response: ")
            except sr.RequestError as e:
                # Try to use a different recognition service if Google fails
                try:
                    error_msg = "Let me try another way to understand you..."
                    print_with_typing(error_msg,
                                    color=Fore.YELLOW if Fore else None)
                    speak(error_msg)
                    response = recognizer.recognize_sphinx(audio)
                    print_with_typing(f"You said: {response}", color=Fore.GREEN if Fore else None)
                    return response
                except Exception:
                    error_msg = "I'm having trouble with the speech recognition. Let's try typing instead:"
                    print_with_typing(error_msg,
                                    color=Fore.RED if Fore else None)
                    speak(error_msg)
                    return input("Your response: ")

def listen_multi(end_phrases=None, max_segments=10, short_timeout=2, phrase_time_limit=40, long_silence_limit=1, language='en-US', is_followup=False):
    """
    Keep listening and appending segments until a long silence or an end phrase is detected.
    Also handles pause/resume, repeat, and skip commands.
    Returns (full_response, segments, command).
    
    A single silence (no speech detected) is now treated as a signal to move on.
    """
    if end_phrases is None:
        end_phrases = []
    
    # Add implicit end phrases - expanded to catch more variations
    implicit_end_phrases = [
        "no", "nope", "no thanks", "no thank you",
        "that's it", "that is it", "thats it",
        "nothing else", "nothing more", "nothing to add",
        "that's all", "that is all", "thats all",
        "i don't want to", "i dont want to", "don't want to", "dont want to",
        "i don't want to share", "i dont want to share",
        "i don't want to answer", "i dont want to answer"
    ]
    for phrase in implicit_end_phrases:
        if phrase not in end_phrases:
            end_phrases.append(phrase)
            
    segments = []
    silence_count = 0
    
    while len(segments) < max_segments:
        # Use a shorter timeout for follow-up questions
        part = listen(timeout=short_timeout, phrase_time_limit=phrase_time_limit, language=language, max_retries=0, is_followup=is_followup).strip().lower()
        
        # Handle special commands
        if part in ["pause", "hold on", "p"]:
            print_with_typing("Interview paused. Say 'resume' or press Enter when ready to continue.", 
                            color=Fore.YELLOW if Fore else None)
            speak("Interview paused. Say resume or press Enter when ready to continue.")
            while True:
                resume = input("Press Enter or say 'resume' to continue: ").strip().lower()
                if resume == "" or resume == "resume" or resume == "r":
                    print_with_typing("Resuming interview...", color=Fore.GREEN if Fore else None)
                    speak("Resuming interview.")
                    break
            continue
            
        if part in ["repeat", "say again", "r"]:
            return "", [], "repeat"
            
        if part in ["skip", "next question", "s"]:
            return "", [], "skip"
            
        if part in ["help", "h"]:
            help_msg = """
            Voice Commands Available:
            • "pause" or "p" - Pause the interview
            • "resume" or "r" - Resume after pause
            • "repeat" or "r" - Repeat the current question
            • "skip" or "s" - Skip to next question
            • "that's all" - Finish your answer
            • "help" or "h" - Show this help message
            """
            print_with_typing(help_msg, color=Fore.CYAN if Fore else None)
            continue
        
        if part:
            # Check if this is a negative response before adding to segments
            if any(phrase in part.lower() for phrase in end_phrases):
                print_with_typing("Understood. Moving on...",
                                color=Fore.YELLOW if Fore else None)
                # Still add the response to segments before breaking
                segments.append(part)
                break
                
            # If it's not a negative response, add it to segments
            segments.append(part)
            break  # <-- Only accept the first non-empty segment and return
        else:
            # If no speech is detected (empty response), treat as a signal to move on immediately
            silence_msg = "I'll take that silence as we're ready to move on."
            print_with_typing(silence_msg,
                            color=Fore.YELLOW if Fore else None)
            speak(silence_msg)
            break
    
    full_response = ' '.join(segments)
    return full_response, segments, None
