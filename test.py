# test_voice.py
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)

engine.say("This is a test of the AI voice system.")
engine.runAndWait()
