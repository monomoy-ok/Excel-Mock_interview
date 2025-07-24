# app/evaluator.py

from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME

client = OpenAI(api_key=OPENAI_API_KEY)

def evaluate_answer(question: str, answer: str) -> str:
    """
    Sends question + user answer to GPT and gets feedback.
    Returns a concise evaluation string.
    """
    prompt = f"""
You are a technical Excel interviewer.

Here is a question:
"{question}"

And the candidate's answer:
"{answer}"

Evaluate this answer on the following:
- Accuracy (is the answer technically correct?)
- Clarity (is it well explained?)
- Completeness (any key point missing?)
Give a short feedback (2-3 lines), and a score out of 10 at the end like "Score: 7/10".
Respond in plain text only.
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=200
        )
        feedback = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"\u26a0\ufe0f LLM API call failed: {e}")
        feedback = "Could not evaluate answer due to a technical issue."
    return feedback
