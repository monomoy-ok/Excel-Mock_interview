# app/counter_question.py
from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME

client = OpenAI(api_key=OPENAI_API_KEY)

def get_counter_question(question: str, answer: str) -> str:
    """
    Use LLM to generate a relevant follow-up (counter) question based on the original question and candidate's answer.
    """
    prompt = f"""
You are an expert interviewer. Given the following interview question and the candidate's answer, generate a single, natural-sounding follow-up question that encourages the candidate to elaborate, clarify, or provide a specific example. Do not repeat the original question. Be concise and conversational.

Original question:
"{question}"

Candidate's answer:
"{answer}"

Follow-up question:
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"\u26a0\ufe0f LLM API call failed: {e}")
        return "Could not generate a follow-up question due to a technical issue."
