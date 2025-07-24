# app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment. Please check your .env file.")

MODEL_NAME = "gpt-4o-mini"  # Or gpt-4o-mini if you're using mini API

INTERVIEW_QUESTIONS_COUNT = 4  # Change to increase/decrease

# Branding and customization
LOGO_TEXT = "Coding Ninjas AI Interview"
PRIMARY_COLOR = "CYAN"  # Options: CYAN, GREEN, YELLOW, etc.
INTRO_TEXT = "Welcome to Coding Ninjas AI Interview System!"

# Audio controls
VOICE_RATE = 145  # Words per minute
VOICE_VOLUME = 1.0  # 0.0 to 1.0
VOICE_PITCH = 1.0  # Not all engines support pitch

# Local model fallback
USE_LOCAL_MODEL = False  # Set to True to use a local LLM instead of OpenAI
LOCAL_MODEL_PATH = "models/llama.bin"  # Path to local model (if used)
