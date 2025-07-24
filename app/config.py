# app/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env (for local development)
load_dotenv()

# Required: OpenAI API Key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables or .env file.")

# Optional: Model and interview settings
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
INTERVIEW_QUESTIONS_COUNT = int(os.environ.get("INTERVIEW_QUESTIONS_COUNT", 4))

# Branding and UI customization
LOGO_TEXT = "Coding Ninjas AI Interview"
PRIMARY_COLOR = "CYAN"  # Options: CYAN, GREEN, YELLOW, etc.
INTRO_TEXT = "Welcome to Coding Ninjas AI Interview System!"

# Audio output settings
VOICE_RATE = 145
VOICE_VOLUME = 1.0
VOICE_PITCH = 1.0

# Optional: Local fallback model settings
USE_LOCAL_MODEL = os.environ.get("USE_LOCAL_MODEL", "False").lower() == "true"
LOCAL_MODEL_PATH = os.environ.get("LOCAL_MODEL_PATH", "models/llama.bin")
