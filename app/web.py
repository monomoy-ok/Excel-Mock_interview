import streamlit as st
import sys
import os

# Ensure the parent directory is in sys.path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm_questions import get_interview_questions
from app.evaluator import evaluate_answer
from app.report_generator import generate_pdf_report
from app.config import INTERVIEW_QUESTIONS_COUNT

st.set_page_config(page_title="Excel Mock Interviewer", layout="centered")
st.title("Excel Mock Interviewer")

if "step" not in st.session_state:
    st.session_state.step = 0
if "questions" not in st.session_state:
    st.session_state.questions = get_interview_questions(INTERVIEW_QUESTIONS_COUNT)
if "answers" not in st.session_state:
    st.session_state.answers = [""] * INTERVIEW_QUESTIONS_COUNT
if "feedback" not in st.session_state:
    st.session_state.feedback = [""] * INTERVIEW_QUESTIONS_COUNT
if "report_path" not in st.session_state:
    st.session_state.report_path = None
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False

if st.session_state.step == 0:
    st.write("Welcome to the Excel Mock Interview! Click below to begin.")
    if st.button("Start Interview"):
        st.session_state.step = 1

elif 1 <= st.session_state.step <= INTERVIEW_QUESTIONS_COUNT:
    idx = st.session_state.step - 1
    st.subheader(f"Question {st.session_state.step}")
    st.write(st.session_state.questions[idx])
    answer = st.text_area("Your Answer:", value=st.session_state.answers[idx], key=f"answer_{idx}")
    if st.button("Submit Answer", key=f"submit_{idx}"):
        st.session_state.answers[idx] = answer
        st.session_state.feedback[idx] = evaluate_answer(st.session_state.questions[idx], answer)
        st.session_state.step += 1

elif st.session_state.step == INTERVIEW_QUESTIONS_COUNT + 1:
    st.write("Interview complete! Generating your report...")
    candidate_name = st.text_input("Enter your name for the report:")
    if st.button("Generate Report"):
        report_path = generate_pdf_report(
            candidate_name=candidate_name or "Candidate",
            questions=st.session_state.questions,
            answers=st.session_state.answers,
            feedbacks=st.session_state.feedback
        )
        st.session_state.report_path = report_path
        st.session_state.interview_complete = True
        st.session_state.step += 1

elif st.session_state.interview_complete:
    st.success("✅ Interview complete. Report successfully generated.")
    if st.session_state.report_path:
        st.write(f"📄 Report saved at: `{st.session_state.report_path}`")
    if st.button("Restart Interview"):
        for key in ["step", "questions", "answers", "feedback", "report_path", "interview_complete"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun() 