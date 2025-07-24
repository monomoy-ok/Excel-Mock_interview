# app/config.py

import os

# Check if running on Streamlit Cloud (via st.secrets)
try:
    import streamlit as st
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    MODEL_NAME = st.secrets.get("MODEL_NAME", "gpt-4o-mini")
    INTERVIEW_QUESTIONS_COUNT = int(st.secrets.get("INTERVIEW_QUESTIONS_COUNT", 4))
except ImportError:
    # Local dev: load from .env
    from dotenv import load_dotenv
    load_dotenv()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in environment or .env file.")

    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
    INTERVIEW_QUESTIONS_COUNT = int(os.getenv("INTERVIEW_QUESTIONS_COUNT", 4))

# Branding and customization
LOGO_TEXT = "Coding Ninjas AI Interview"
PRIMARY_COLOR = "CYAN"  # Options: CYAN, GREEN, YELLOW, etc.
INTRO_TEXT = "Welcome to Coding Ninjas AI Interview System!"

# Audio controls
VOICE_RATE = 145
VOICE_VOLUME = 1.0
VOICE_PITCH = 1.0

# Local model fallback (optional)
USE_LOCAL_MODEL = False
LOCAL_MODEL_PATH = "models/llama.bin"
