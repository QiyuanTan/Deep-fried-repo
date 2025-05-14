import json
from http.client import responses
from pydoc_data.topics import topics

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.constants import START
from langgraph.graph import StateGraph

from llm import get_llm
from nodes.autograder_generator.autograder import build_autograder_node
from nodes.validator import validator
from state_types import *

load_dotenv()
llm = get_llm()

graph_builder = StateGraph(State)

def get_notes():
    return ""

def summarizer(state: State):
    # Summarize the question and context
    with open("summarizer_prompt.txt", "r") as f:
        prompt = f.read()

    messages = [
        SystemMessage(prompt),
        HumanMessage(get_notes()),
    ]

    response = llm.invoke(messages)

    state["notes_summary"] = response.content
    return {"messages": AIMessage("some additional comments about the notes_summary")}

def generator(state: State):
    if not state["curr_question_valid"]:
        # regenerate a single question

        state["curr_question_valid"] = True
        return {"messages": AIMessage(f"regenerated question {state['current_index']}")}
    else:
        # generate all questions

        return {"messages": AIMessage("generated all questions")}

autograder_node = build_autograder_node(llm)

graph_builder.add_node("summarizer", summarizer)
graph_builder.add_node("generator", generator)
graph_builder.add_node("autograder_generator", autograder_node)
graph_builder.add_node("validator", validator)

graph_builder.add_edge(START, "summarizer")
graph_builder.add_edge("summarizer", "generator")
graph_builder.add_edge("generator", "autograder_generator")
graph_builder.add_edge("autograder_generator", "validator")
graph_builder.add_conditional_edges("validator", lambda state: state["__next__"])

graph = graph_builder.compile()

final_state = graph.invoke({
    "questions": [],
    "num_questions": 5,
    "current_index": 0,
    "notes_summary": ["topic1", "topic2"],
    "curr_question_valid": True,
    "messages": [
    ]},
    {"recursion_limit": 1000})
for message in final_state['messages']:
    print(message.content)