# app/nodes.py

from app.llm_questions import get_interview_questions
from app.evaluator import evaluate_answer
from app.report_generator import generate_pdf_report
from app.config import MODEL_NAME, OPENAI_API_KEY, INTERVIEW_QUESTIONS_COUNT
from app.voice_utils import speak, listen, listen_multi
from app.counter_question import get_counter_question
from app.utils import print_with_typing, log_event, translate_text
import pyttsx3
try:
    from colorama import Fore
except ImportError:
    Fore = None
from openai import OpenAI
client = OpenAI()
from typing import TypedDict, List, Optional
import random
from app.question_bank import get_random_questions, get_question_by_difficulty, QUESTIONS

friendly_transitions = [
    "Great! Let’s move on to the next question.",
    "Awesome, here’s another one.",
    "Thanks for that answer. Next question coming up!",
    "Let’s try the next question.",
]

def get_friendly_transition():
    return random.choice(friendly_transitions)

class InterviewState(TypedDict, total=False):
    questions: List[str]
    current_question: int
    answers: List[str]
    feedback: List[str]
    complete: bool
    report: Optional[str]
    name: str
    intro: str
    language: str
    summaries: List[str]
    encouragements: List[str]
    followups: List[dict]
    followup_summaries: List[str]
    followup_encouragements: List[str]
    difficulty: str
    is_experienced: bool

def get_lang_code(language):
    return ('en', 'en-US')

# Utility: Get user input with fallback
def get_user_response(prompt_text, rec_lang='en-US'):
    try:
        if prompt_text.strip():
            speak(prompt_text)
        print_with_typing("Listening...")
        response = listen(language=rec_lang).strip()
        response = response.lower()
        if not response:
            raise ValueError("Voice input failed")
        print_with_typing(f"Candidate said: {response}")
        return response
    except:
        print_with_typing("Couldn't capture voice. Please type your answer instead:")
        typed = input("Your Answer: ").strip()
        print_with_typing(f"Candidate typed: {typed}")
        return typed

def llm_extract_name(raw_input):
    system_msg = "You are a helpful assistant. Extract only the person's first name from the following sentence. If the name is not clear, just return the whole input."
    prompt = f"Sentence: \"{raw_input}\"\nName (one or two words only):"
    try:
        for _ in range(2):  # Try up to 2 times for best accuracy
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=10
            )
            name = response.choices[0].message.content.strip().split("\n")[0]
            # Post-process to remove common prefixes
            lowered = name.lower()
            for prefix in ["my name is", "i am", "this is", "it's", "name is", "the name is", "myself", "me is", "me", "i'm", "iam", "call me", "they call me", "you can call me"]:
                if lowered.startswith(prefix):
                    name = name[len(prefix):].strip()
                    break
            # Only keep the first two words (in case of "first last")
            name = " ".join(name.split()[:2])
            # If the result still looks like a phrase, re-prompt with just this part
            if any(p in name.lower() for p in ["name", "is", "am", "this", "call", "myself"]):
                prompt = f"Extract only the person's first name from: '{name}'\nName (one or two words only):"
                continue
            return name.title()
        return name.title()
    except Exception as e:
        print_with_typing(f"[LLM error extracting name: {e}]", color=Fore.RED if Fore else None)
        return raw_input.title()

def llm_summarize_and_encourage(answer):
    from openai import OpenAI
    from app.config import MODEL_NAME, OPENAI_API_KEY
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_msg = "You are a friendly interviewer. Summarize and encourage the candidate."
    prompt = f"Here is the candidate's answer:\n---\n{answer}\n---\n1. Summarize their answer in 1-2 sentences.\n2. Give a short, positive encouragement or comment.\nRespond as: SUMMARY: ...\nENCOURAGEMENT: ..."
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=120
        )
        content = response.choices[0].message.content.strip()
        summary = ""
        encouragement = ""
        for line in content.split("\n"):
            if line.strip().lower().startswith("summary:"):
                summary = line.split(":",1)[-1].strip()
            if line.strip().lower().startswith("encouragement:"):
                encouragement = line.split(":",1)[-1].strip()
        return summary, encouragement
    except Exception as e:
        return "", "Great job!"

def print_progress(current, total):
    msg = f"Progress: Question {current} of {total}"
    print_with_typing(msg, color=Fore.BLUE if Fore else None)
    # Optionally, speak the progress
    # speak(msg)

def listen_multi_with_commands(prompt, end_phrases=None, max_segments=10, short_timeout=2, phrase_time_limit=40, long_silence_limit=2):
    """
    Like listen_multi, but recognizes 'repeat', 'skip', 'pause', 'resume' commands and falls back to text input if needed.
    Returns (full_response, segments, command) where command is one of None, 'repeat', 'skip', 'pause'.
    """
    if end_phrases is None:
        end_phrases = []
    segments = []
    silence_count = 0
    last_prompt = prompt
    while len(segments) < max_segments:
        part = listen(timeout=short_timeout, phrase_time_limit=phrase_time_limit).strip().lower()
        if part:
            if part in ["repeat", "can you repeat", "say again"]:
                return "", [], "repeat"
            if part in ["skip", "next question"]:
                return "", [], "skip"
            if part in ["pause", "hold on"]:
                print_with_typing("Interview paused. Say 'resume' to continue.", color=Fore.YELLOW if Fore else None)
                speak("Interview paused. Say resume to continue.")
                while True:
                    resume = listen(timeout=10, phrase_time_limit=5).strip().lower()
                    if resume == "resume":
                        print_with_typing("Resuming interview...", color=Fore.YELLOW if Fore else None)
                        speak("Resuming interview.")
                        break
                continue
            segments.append(part)
            silence_count = 0
            if any(phrase in part for phrase in end_phrases):
                break
        else:
            silence_count += 1
            if silence_count >= long_silence_limit:
                break
    if not segments:
        # Fallback to text input
        print_with_typing("Couldn't capture voice. Please type your answer instead:", color=Fore.YELLOW if Fore else None)
        typed = input("Your Answer: ").strip()
        if typed.lower() in ["repeat", "can you repeat", "say again"]:
            return "", [], "repeat"
        if typed.lower() in ["skip", "next question"]:
            return "", [], "skip"
        segments = [typed]
    full_response = ' '.join(segments)
    return full_response, segments, None

def llm_intro_followup(intro_so_far):
    system_msg = "You are a friendly interviewer."
    prompt = f"The candidate is introducing themselves for an interview. Here is what they have said so far:\n---\n{intro_so_far}\n---\nSuggest a short, conversational follow-up question to encourage them to share more about themselves. If it sounds like they are done, ask if they want to add anything else or if they're finished."
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=60
        )
        followup = response.choices[0].message.content.strip()
        return followup
    except Exception as e:
        print_with_typing(f"[LLM error in intro followup: {e}]", color=Fore.RED if Fore else None)
        return "Would you like to add anything else about yourself, or are you finished?"

def stream_llm_response(prompt, language, tts_lang):
    from openai import OpenAI
    from app.config import MODEL_NAME, OPENAI_API_KEY
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=120,
            stream=True
        )
        full_text = ""
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                part = chunk.choices[0].delta.content
                print(part, end='', flush=True)
                full_text += part
        print()
        # Speak the full response at the end
        speak(translate_text(full_text, language), language=tts_lang)
        return full_text
    except Exception as e:
        print(f"[Streaming LLM error: {e}]")
        return ""

# Node 1: Introductory message
def intro_node(state: InterviewState) -> InterviewState:
    language = 'english'
    tts_lang, rec_lang = get_lang_code(language)
    # Prompt for candidate name
    name_prompt = translate_text("Before we begin, could you please tell me your name?", language)
    print_with_typing(name_prompt, color=Fore.CYAN if Fore else None)
    speak(name_prompt, language=tts_lang)
    raw_name = get_user_response("", rec_lang)
    candidate_name = llm_extract_name(raw_name)
    log_event(f"Candidate provided name: {candidate_name}")
    intro_message = translate_text(
        f"Hello {candidate_name}, I am the Excel AI interviewer built for interviewing candidates in Coding Ninjas. Let's get to know you a bit before we start. Could you please introduce yourself?and when you're finished, just say 'That's all for my introduction.'",
        language)
    log_event(f"Started interview with {candidate_name}")
    print_with_typing(intro_message, color=Fore.CYAN if Fore else None)
    speak(intro_message, language=tts_lang)
    import time
    time.sleep(1.0)
    end_phrases = [
        "that's all for my introduction", "that's all", "that is all", "i'm done", "i am done", "no more", "nothing else",
        "that's it from my side", "that is it from my side", "that's it", "that is it"
    ]
    # Only prompt and listen once
    intro_parts = []
    full_response, segments, _ = listen_multi(
        end_phrases=end_phrases,
        max_segments=10,
        short_timeout=3,
        phrase_time_limit=60,
        long_silence_limit=1,  # 2 seconds
        language=rec_lang
    )
    if not segments:
        print_with_typing("No response detected. Please try again.", color=Fore.YELLOW if Fore else None)
        speak("No response detected. Please try again.", language=tts_lang)
        # Retry once only if the first attempt was silent
        full_response, segments, _ = listen_multi(
            end_phrases=end_phrases,
            max_segments=10,
            short_timeout=3,
            phrase_time_limit=60,
            long_silence_limit=1,
            language=rec_lang
        )
        if not segments:
            print_with_typing("Couldn't capture voice. Please type your introduction instead:", color=Fore.YELLOW if Fore else None)
            typed = input("Your Introduction: ").strip()
            intro_parts = [typed]
        else:
            intro_parts.extend(segments)
    else:
        intro_parts.extend(segments)
    # Remove any end_phrases from the final intro
    intro_response = ' '.join(intro_parts)
    for phrase in end_phrases:
        intro_response = intro_response.replace(phrase, '')
    intro_response = intro_response.strip()

    # Remove keyword-based detection, use LLM to classify experience
    def llm_detect_experience(intro_text):
        prompt = f"""
You are an interview assistant. Based on the following candidate introduction, classify them as either 'experienced' (if they have any work, internship, or professional experience) or 'fresher' (if they have no such experience). Respond with only one word: 'experienced' or 'fresher'.

Introduction: """
        prompt += f"{intro_text}\n"
        prompt += "\nClassification:"
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=2
            )
            result = response.choices[0].message.content.strip().lower()
            if 'experienced' in result:
                return True
            elif 'fresher' in result:
                return False
            else:
                return None
        except Exception as e:
            print_with_typing(f"[LLM error detecting experience: {e}]", color=Fore.RED if Fore else None)
            return None

    is_experienced = llm_detect_experience(intro_response)
    # If LLM cannot determine, ask the candidate directly
    if is_experienced is None:
        ask_exp = translate_text("Do you have any work or internship experience? Please answer yes or no.", language)
        print_with_typing(ask_exp, color=Fore.YELLOW if Fore else None)
        speak(ask_exp, language=tts_lang)
        # Use listen directly for better control
        from app.voice_utils import listen
        exp_response = ""
        retries = 0
        while retries < 2:
            exp_response = listen(timeout=3, phrase_time_limit=10, language=rec_lang, max_retries=0).strip().lower()
            if exp_response:
                break
            retries += 1
        if not exp_response:
            print_with_typing("Couldn't capture voice. Please type your answer instead:", color=Fore.YELLOW if Fore else None)
            exp_response = input("Your Answer: ").strip().lower()
        yes_variants = ["yes", "yeah", "yep", "i do", "of course", "y", "sure"]
        no_variants = ["no", "nope", "not yet", "never", "n"]
        if any(word in exp_response for word in yes_variants):
            is_experienced = True
        elif any(word in exp_response for word in no_variants):
            is_experienced = False
        else:
            # Default to fresher if unclear
            is_experienced = False

    thank_you = translate_text(f"Thank you for sharing, {candidate_name}! That was a great introduction.", language)
    print_with_typing(thank_you, color=Fore.GREEN if Fore else None)
    log_event(f"Candidate introduction: {intro_response}")
    speak(thank_you + " Now, let's start the interview questions.", language=tts_lang)
    import random
    num_questions = INTERVIEW_QUESTIONS_COUNT
    static_count = num_questions // 2
    llm_count = num_questions - static_count
    if is_experienced:
        # Experienced: ask about intermediate and advanced
        all_exp = QUESTIONS["intermediate"] + QUESTIONS["advanced"]
        static_questions = random.sample(all_exp, min(static_count, len(all_exp)))
        llm_questions = get_interview_questions(n=llm_count, topic="Excel advanced projects")
    else:
        # Fresher: ask about basics
        static_questions = random.sample(QUESTIONS["basic"], min(static_count, len(QUESTIONS["basic"])))
        llm_questions = get_interview_questions(n=llm_count, topic="Excel formulas basics")
    all_questions = static_questions + llm_questions
    random.shuffle(all_questions)
    return {
        "questions": all_questions,
        "current_question": 0,
        "answers": [],
        "feedback": [],
        "complete": False,
        "report": None,
        "name": candidate_name,
        "intro": intro_response,
        "language": language,
        "is_experienced": is_experienced
    }

# Node 2: Ask the next question
def ask_question_node(state: InterviewState) -> InterviewState:
    language = 'english'
    tts_lang, rec_lang = get_lang_code(language)
    question_number = state["current_question"] + 1
    total_questions = len(state["questions"])
    # Friendly transition (except for first question)
    if question_number > 1:
        transition_msg = get_friendly_transition()
        print_with_typing(transition_msg, color=Fore.CYAN if Fore else None)
        speak(transition_msg, language=tts_lang)
    print_progress(question_number, total_questions)
    question = state["questions"][state["current_question"]]
    printed_prompt = translate_text(f"Question {question_number}: {question}", language)
    print_with_typing(printed_prompt, color=Fore.YELLOW if Fore else None)
    speak(printed_prompt, language=tts_lang)
    import time
    time.sleep(1.5)

    # Multi-turn, conversational answer capture (truly conversational)
    answer_parts = []
    end_phrases = ["that's all for my answer", "that's all", "that is all", "i'm done", "i am done", "no more", "nothing else", "that's it from my side", "that is it from my side", "that's it", "that is it"]
    uncertainty_phrases = [
        "i don't know", "dont know", "don't know", "i dont know",
        "i don't remember", "dont remember", "don't remember", "i dont remember",
        "i forgot", "forgot", "no idea", "not sure", "sorry"
    ]
    encouragements = [
        "Thanks for sharing that!",
        "That's helpful! Please continue if you'd like.",
        "Great, feel free to add more if you wish."
    ]
    followups = [
        "You can continue, or say 'That's all for my answer' if you're finished."
    ]
    turn = 0
    # --- ASK QUESTION NODE ---
    answer_parts = []
    full_response, segments, command = listen_multi(
        end_phrases=end_phrases,
        max_segments=10,
        short_timeout=3,
        phrase_time_limit=45,
        long_silence_limit=1,  # 2 seconds
        language=rec_lang
    )
    if not segments:
        print_with_typing("No response detected. Please try again.", color=Fore.YELLOW if Fore else None)
        speak("No response detected. Please try again.", language=tts_lang)
        # Retry once only if the first attempt was silent
        full_response, segments, command = listen_multi(
            end_phrases=end_phrases,
            max_segments=10,
            short_timeout=3,
            phrase_time_limit=45,
            long_silence_limit=1,
            language=rec_lang
        )
        if not segments:
            print_with_typing("No response detected. Moving to the next question.", color=Fore.YELLOW if Fore else None)
            speak("No response detected. Moving to the next question.", language=tts_lang)
            state["answers"].append("")
            return state
        # Only process the first non-empty answer, do not listen again
        answer_parts = segments
    else:
        answer_parts = segments
    # No further listening or retry after a valid answer
    user_input = ' '.join(answer_parts)
    for phrase in end_phrases:
        user_input = user_input.replace(phrase, '')
    user_input = user_input.strip()
    state["answers"].append(user_input)

    # LLM summary and encouragement
    summary, encouragement = llm_summarize_and_encourage(user_input)
    state.setdefault("summaries", []).append(summary)
    state.setdefault("encouragements", []).append(encouragement)
    if encouragement:
        encouragement_translated = translate_text(encouragement, language)
        print_with_typing(encouragement_translated, color=Fore.CYAN if Fore else None)
        speak(encouragement_translated, language=tts_lang)

    # Adaptive difficulty: parse last feedback for score and adjust
    if state.get("feedback"):
        import re
        last_feedback = state["feedback"][-1]
        match = re.search(r"score\s*[:=]\s*(\d+)[/\-]?(10)?", last_feedback.lower())
        score = int(match.group(1)) if match else 6
        if score >= 8:
            state["difficulty"] = "advanced"
        elif score <= 5:
            state["difficulty"] = "basic"
        else:
            state["difficulty"] = "intermediate"
    # Ensure 'difficulty' is always set before using
    if "difficulty" not in state:
        state["difficulty"] = "basic"
    # Remove this block to prevent question repetition:
    # if state["current_question"] + 1 < len(state["questions"]):
    #     next_q = get_question_by_difficulty(state["difficulty"])
    #     state["questions"][state["current_question"] + 1] = next_q

    return state

# Node 3: Evaluate response and store feedback (do not speak yet)
def evaluate_node(state: InterviewState) -> InterviewState:
    answer = state["answers"][-1]
    question = state["questions"][state["current_question"]]
    feedback = evaluate_answer(question, answer)
    log_event(f"Evaluated answer: {answer} | Feedback: {feedback}")
    state["feedback"].append(feedback)
    state["current_question"] += 1
    return state

# Node 4: Summarize all feedback and generate report
def summarize_node(state: InterviewState) -> InterviewState:
    language = 'english'
    final_msg = translate_text("Interview complete. Generating your performance summary...", language)
    print_with_typing(final_msg, color=Fore.CYAN if Fore else None)
    log_event("Interview complete. Generating summary and report.")
    speak(final_msg, language=get_lang_code(language)[0])

    print_with_typing(translate_text("Interview Summary & Feedback:\n", language), color=Fore.CYAN if Fore else None)
    for i, fb in enumerate(state["feedback"], 1):
        print_with_typing(translate_text(f"Q{i} Feedback: {fb}\n", language), color=Fore.GREEN if Fore else None)

    report_path = generate_pdf_report(
        candidate_name=state["name"],
        questions=state["questions"],
        answers=state["answers"],
        feedbacks=state["feedback"],
        summaries=state.get("summaries"),
        encouragements=state.get("encouragements")
    )

    state["report"] = report_path
    state["complete"] = True
    print_with_typing(translate_text(f"Report saved at: {report_path}", language), color=Fore.CYAN if Fore else None)
    log_event(f"Report generated at: {report_path}")
    speak(translate_text("Your report has been saved. Thank you for completing the interview.", language), language=get_lang_code(language)[0])

    # --- New: Ask if candidate has any questions ---
    ask_q = "Do you have any questions about this interview or about Coding Ninjas? If yes, please ask now. If not, you can say 'no'."
    print_with_typing(ask_q, color=Fore.YELLOW if Fore else None)
    speak(ask_q, language=get_lang_code(language)[0])
    from app.voice_utils import listen
    user_q = listen(timeout=3, phrase_time_limit=30, language=get_lang_code(language)[1], max_retries=0).strip()
    if user_q and user_q.lower() not in ["no", "nope", "none", "nah"]:
        print_with_typing(f"You asked: {user_q}", color=Fore.GREEN if Fore else None)
        # LLM call to answer the candidate's question
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        system_msg = "You are a helpful Coding Ninjas interview assistant."
        prompt = f"Answer the candidate's question about the interview or Coding Ninjas.\n\nQuestion: {user_q}\nAnswer:"
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=120
            )
            answer = response.choices[0].message.content.strip()
            print_with_typing(answer, color=Fore.CYAN if Fore else None)
            speak(answer, language=get_lang_code(language)[0])
        except Exception as e:
            print_with_typing("Sorry, I couldn't answer your question right now.", color=Fore.RED if Fore else None)
            speak("Sorry, I couldn't answer your question right now.", language=get_lang_code(language)[0])
    else:
        print_with_typing("No questions from candidate.", color=Fore.YELLOW if Fore else None)

    # Inform about HR follow-up
    hr_msg = "If you are selected for the next round, you will receive a call from our HR department within a week."
    print_with_typing(hr_msg, color=Fore.GREEN if Fore else None)
    speak(hr_msg, language=get_lang_code(language)[0])

    return state

def followup_node(state: InterviewState) -> InterviewState:
    """
    After the main answer, use the LLM to generate a personalized follow-up question, listen for a multi-turn response, and append it to the state.
    """
    language = 'english'
    tts_lang, rec_lang = get_lang_code(language)
    question_number = state["current_question"] + 1
    total_questions = len(state["questions"])
    print_progress(question_number, total_questions)
    question = state["questions"][state["current_question"]]
    answer = state["answers"][-1] if state["answers"] else ""
    # Use LLM to generate a follow-up prompt
    # Use is_experienced to tailor follow-up
    is_experienced = state.get("is_experienced", False)
    if is_experienced:
        followup_prompt = f"You are a friendly interviewer. The candidate just answered the following question:\n\nQuestion: {question}\nAnswer: {answer}\n\nGenerate a single, natural-sounding follow-up question about their work experience, a project, or a challenge they faced using Excel in a professional context."
    else:
        followup_prompt = f"You are a friendly interviewer. The candidate just answered the following question:\n\nQuestion: {question}\nAnswer: {answer}\n\nGenerate a single, natural-sounding follow-up question about Excel formulas, functions, or learning experiences for a fresher."
    from openai import OpenAI
    from app.config import MODEL_NAME, OPENAI_API_KEY
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": followup_prompt}],
            temperature=0.7,
            max_tokens=60
        )
        followup_q = response.choices[0].message.content.strip()
    except Exception as e:
        followup_q = "Can you tell me a bit more about that?"
    followup_q_translated = translate_text(followup_q, language)
    print_with_typing(f"Follow-up: {followup_q_translated}", color=Fore.MAGENTA if Fore else None)
    speak(followup_q_translated, language=tts_lang)
    import time
    time.sleep(1.0)
    end_phrases = ["that's all for my answer", "that's all", "that is all", "i'm done", "i am done", "no more", "nothing else"]
    uncertainty_phrases = [
        "i don't know", "dont know", "don't know", "i dont know",
        "i don't remember", "dont remember", "don't remember", "i dont remember",
        "i forgot", "forgot", "no idea", "not sure", "sorry"
    ]
    # --- FOLLOWUP NODE ---
    full_response, segments, command = listen_multi(
        end_phrases=end_phrases,
        max_segments=10,
        short_timeout=3,
        phrase_time_limit=45,
        long_silence_limit=1,  # 2 seconds
        language=rec_lang
    )
    if not segments:
        print_with_typing("No response detected. Please try again.", color=Fore.YELLOW if Fore else None)
        speak("No response detected. Please try again.", language=tts_lang)
        # Retry once only if the first attempt was silent
        full_response, segments, command = listen_multi(
            end_phrases=end_phrases,
            max_segments=10,
            short_timeout=3,
            phrase_time_limit=45,
            long_silence_limit=1,
            language=rec_lang
        )
        if not segments:
            print_with_typing("No response detected. Moving to the next question.", color=Fore.YELLOW if Fore else None)
            speak("No response detected. Moving to the next question.", language=tts_lang)
            state.setdefault("followups", []).append({
                "question": question,
                "answer": answer,
                "followup_question": followup_q_translated,
                "followup_answer": ""
            })
            return state
        # Only process the first non-empty answer, do not listen again
        segments_to_use = segments
    else:
        segments_to_use = segments
    # No further listening or retry after a valid answer
    state.setdefault("followups", []).append({
        "question": question,
        "answer": answer,
        "followup_question": followup_q_translated,
        "followup_answer": ' '.join(segments_to_use)
    })
    # LLM summary and encouragement for follow-up
    summary, encouragement = llm_summarize_and_encourage(' '.join(segments_to_use))
    state.setdefault("followup_summaries", []).append(summary)
    state.setdefault("followup_encouragements", []).append(encouragement)
    if encouragement:
        encouragement_translated = translate_text(encouragement, language)
        print_with_typing(encouragement_translated, color=Fore.CYAN if Fore else None)
        speak(encouragement_translated, language=tts_lang)
    return state

def speak(text: str, language='en-US'):
    """Speak out the given text using pyttsx3."""
    print(f"🗣️ AI says: {text}")
    engine = pyttsx3.init(driverName='sapi5')
    voices = engine.getProperty('voices')
    # Prefer Zira (female), then David (male), else first available
    selected_voice = None
    for v in voices:
        if 'zira' in v.name.lower():
            selected_voice = v.id
            break
    if not selected_voice:
        for v in voices:
            if 'david' in v.name.lower():
                selected_voice = v.id
                break
    if not selected_voice and voices:
        selected_voice = voices[0].id
    if selected_voice:
        engine.setProperty('voice', selected_voice)
    engine.setProperty('rate', 145)  # slower, more natural
    engine.setProperty('volume', 1.0)
    engine.say(text)
    engine.runAndWait()

