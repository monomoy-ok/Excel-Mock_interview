import streamlit as st
import sys
import os
from st_speech_to_text import st_speech_to_text

# Ensure the parent directory is in sys.path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm_questions import get_interview_questions
from app.evaluator import evaluate_answer
from app.report_generator import generate_pdf_report
from app.config import INTERVIEW_QUESTIONS_COUNT

# Helper for browser-based text-to-speech
def speak_text(text):
    st.write(f"<script>window.speechSynthesis.speak(new SpeechSynthesisUtterance({repr(text)}));</script>", unsafe_allow_html=True)

st.set_page_config(page_title="Excel Mock Interviewer", layout="centered")
st.title("Excel Mock Interviewer (with Voice)")

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
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

if st.session_state.step == 0:
    welcome = "Welcome to the Excel Mock Interview! Click below to begin."
    st.write(welcome)
    if st.session_state.last_spoken != welcome:
        speak_text(welcome)
        st.session_state.last_spoken = welcome
    if st.button("Start Interview"):
        st.session_state.step = 1

elif 1 <= st.session_state.step <= INTERVIEW_QUESTIONS_COUNT:
    idx = st.session_state.step - 1
    question = st.session_state.questions[idx]
    st.subheader(f"Question {st.session_state.step}")
    st.write(question)
    if st.session_state.last_spoken != question:
        speak_text(question)
        st.session_state.last_spoken = question
    st.write("You can answer by typing or using your voice:")
    # Voice input
    voice_text = st_speech_to_text(language='en', use_container_width=True)
    # Text input
    answer = st.text_area("Your Answer:", value=st.session_state.answers[idx], key=f"answer_{idx}")
    # Prefer voice input if available
    if voice_text and voice_text != answer:
        answer = voice_text
        st.session_state.answers[idx] = answer
        st.success(f"Voice recognized: {voice_text}")
    if st.button("Submit Answer", key=f"submit_{idx}"):
        st.session_state.answers[idx] = answer
        feedback = evaluate_answer(st.session_state.questions[idx], answer)
        st.session_state.feedback[idx] = feedback
        st.session_state.step += 1
        st.session_state.last_spoken = ""
        # Speak feedback after advancing
        st.session_state.feedback_to_speak = feedback
        st.experimental_rerun()
    # Speak feedback if just advanced
    if "feedback_to_speak" in st.session_state and st.session_state.feedback_to_speak:
        speak_text(st.session_state.feedback_to_speak)
        st.session_state.feedback_to_speak = ""

elif st.session_state.step == INTERVIEW_QUESTIONS_COUNT + 1:
    complete_msg = "Interview complete! Generating your report..."
    st.write(complete_msg)
    if st.session_state.last_spoken != complete_msg:
        speak_text(complete_msg)
        st.session_state.last_spoken = complete_msg
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
        st.session_state.last_spoken = ""
        st.experimental_rerun()

elif st.session_state.interview_complete:
    done_msg = "✅ Interview complete. Report successfully generated."
    st.success(done_msg)
    if st.session_state.last_spoken != done_msg:
        speak_text(done_msg)
        st.session_state.last_spoken = done_msg
    if st.session_state.report_path:
        st.write(f"📄 Report saved at: `{st.session_state.report_path}`")
    if st.button("Restart Interview"):
        for key in ["step", "questions", "answers", "feedback", "report_path", "interview_complete", "last_spoken", "feedback_to_speak"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun() 