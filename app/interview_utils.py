# app/interview_utils.py

from datetime import datetime
from app.utils import print_with_typing
from openai import OpenAI
from app.config import MODEL_NAME, OPENAI_API_KEY

# Set up OpenAI client
client = OpenAI()

def conversation_invoke(prompt):
    """Invoke the OpenAI API with a prompt and return the response."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM error: {e}]")
        return ""
try:
    from colorama import Fore, Style
except ImportError:
    Fore = Style = None

def print_progress(current, total):
    """Display a visual progress bar for the interview."""
    progress = int((current / total) * 20)
    bar = "█" * progress + "░" * (20 - progress)
    percentage = int((current / total) * 100)
    msg = f"\nProgress: [{bar}] {percentage}% ({current}/{total} questions)"
    print_with_typing(msg, color=Fore.BLUE if Fore else None)

def get_smart_hint(question, previous_answers, difficulty_level):
    """Generate a context-aware hint based on the question and previous answers."""
    hint_prompt = f"""
    Based on the candidate's previous answers:
    {previous_answers}
    
    Generate a helpful hint for this {difficulty_level}-level Excel question:
    {question}
    
    Rules for the hint:
    1. Make it subtle but useful
    2. Don't give away the full answer
    3. Focus on guiding principles or related concepts
    4. If the candidate seems to know the topic but is stuck, give a more specific hint
    5. If the candidate seems unfamiliar, give a more basic conceptual hint
    
    Respond with just the hint, no additional text.
    """
    return conversation_invoke(hint_prompt)

def evaluate_confidence(question, answer):
    """Evaluate the candidate's confidence in their answer."""
    confidence_prompt = f"""
    Rate the candidate's confidence in answering this question on a scale of 1-5:
    Question: {question}
    Answer: {answer}
    
    Score 1-5 where:
    1: Very uncertain, many hesitations
    2: Somewhat uncertain, needs prompting
    3: Moderate confidence, some hesitation
    4: Good confidence, clear explanation
    5: Very confident, clear and authoritative
    
    Only return the number.
    """
    try:
        confidence = int(conversation_invoke(confidence_prompt))
        return confidence
    except:
        return 3  # Default to moderate confidence if evaluation fails

def add_note(state, note_text):
    """Add a timestamped note to the interview state."""
    if 'notes' not in state:
        state['notes'] = []
    note = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'note': note_text
    }
    state['notes'].append(note)
    return state

def get_encouragement(confidence_score, previous_encouragements=None):
    """Generate a contextual encouragement based on confidence score."""
    if previous_encouragements is None:
        previous_encouragements = []
    
    encouragement_prompt = f"""
    Generate a short, natural encouragement for a candidate who just answered with confidence level {confidence_score}/5.
    Previous encouragements used: {previous_encouragements}
    Rules:
    1. Keep it brief and conversational
    2. Don't repeat previous encouragements
    3. Match the tone to their confidence level
    4. For low confidence (1-2), be more supportive
    5. For high confidence (4-5), be more affirming
    
    Respond with just the encouragement, no additional text.
    """
    return conversation_invoke(encouragement_prompt)

def auto_save_state(state):
    """Mark the state for auto-saving."""
    state['last_auto_save'] = datetime.now()
    state['needs_save'] = True
    return state
