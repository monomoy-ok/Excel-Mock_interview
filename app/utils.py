# app/utils.py

import sys
import time
import logging
import os
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# Ensure log directory exists
os.makedirs('data/logs', exist_ok=True)

logging.basicConfig(
    filename='data/logs/app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def log_event(message):
    logging.info(message)

def print_with_typing(text, delay=0.02, color=None):
    """Print text with typing animation effect. Optionally colorize output if colorama is available. Instantly print long outputs."""
    if len(text) > 200:
        # Instantly print long outputs
        if color and COLORAMA_AVAILABLE:
            print(f"{color}{text}{Style.RESET_ALL}")
        else:
            print(text)
        return
    if color and COLORAMA_AVAILABLE:
        for char in text:
            print(f"{color}{char}{Style.RESET_ALL}", end='', flush=True)
            time.sleep(delay)
        print()
    else:
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

def translate_text(text, target_language):
    if target_language.lower() == "english":
        return text
    from openai import OpenAI
    from app.config import MODEL_NAME, OPENAI_API_KEY
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"Translate the following text to {target_language.title()}:\n\n{text}"
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return text

def get_lang_code(language):
    lang_map = {
        'english': ('en', 'en-US'),
        'hindi': ('hi', 'hi-IN'),
        'spanish': ('es', 'es-ES'),
        'french': ('fr', 'fr-FR'),
    }
    return lang_map.get(language.lower(), ('en', 'en-US'))
