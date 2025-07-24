# app/interview_graph.py

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from app.nodes import intro_node, ask_question_node, followup_node, evaluate_node, summarize_node, InterviewState
from app.config import INTERVIEW_QUESTIONS_COUNT

def build_interview_graph() -> RunnableLambda:
    sg = StateGraph(InterviewState)

    sg.add_node("intro", RunnableLambda(intro_node))
    sg.add_node("ask_question", RunnableLambda(ask_question_node))
    sg.add_node("followup", RunnableLambda(followup_node))
    sg.add_node("evaluate_response", RunnableLambda(evaluate_node))
    sg.add_node("summarize", RunnableLambda(summarize_node))

    sg.set_entry_point("intro")
    sg.add_edge("intro", "ask_question")
    sg.add_edge("ask_question", "followup")
    sg.add_edge("followup", "evaluate_response")

    sg.add_conditional_edges(
        "evaluate_response",
        lambda state: (
            "ask_question"
            if state["current_question"] < len(state.get("questions", []))
            else "summarize"
        ),
    )

    sg.add_edge("summarize", END)

    return sg.compile()
