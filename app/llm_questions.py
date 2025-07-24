# app/llm_questions.py
from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME

client = OpenAI()

def get_interview_questions(n=3, topic="Excel"):
    prompt = f"""
You are an expert interviewer. Generate {n} unique, non-repetitive, and relevant interview questions for a candidate on the topic of {topic}. Number each question. Respond with only the questions, one per line, no extra text.
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        questions = [q.strip().split('. ',1)[-1] for q in response.choices[0].message.content.strip().split('\n') if q.strip()]
        return questions[:n]
    except Exception as e:
        print(f"\u26a0\ufe0f LLM API call failed: {e}")
        return ["Could not generate question due to a technical issue."] * n
