import json

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.constants import START
from langgraph.graph import StateGraph

from llm import get_llm
from nodes.autograder_generator.autograder import build_autograder_node
from nodes.validator import validator
from state_types import State

load_dotenv()
llm = get_llm()

def generate_questions(get_notes, get_syllabus):

    graph_builder = StateGraph(State)

    def summarizer(state: State):
        # Summarize the question and context
        with open("summarizer_prompt.txt", "r") as f:
            prompt = f.read()

        messages = [
            SystemMessage(prompt),
            HumanMessage(f"Here's the syllabus of my course {get_syllabus()}. \n"
                         f"Here's my notes{get_notes()}"),
        ]

        response = llm.invoke(messages)

        state["notes_summary"] = response.content
        return {"messages": AIMessage("some additional comments about the notes_summary")}

    def generator(state: State):
        with open("summarizer_prompt.txt", "r") as f:
            prompt = f.read()

        if not state["curr_question_valid"]:
            # regenerate a single question
            messages = [
                SystemMessage(prompt),
                HumanMessage(state["notes_summary"]),
                AIMessage(state["questions"]),
                SystemMessage(f"One of questions you generated is invalid. You need to regenerate it and format it as the following format:" # TODO: json format
                              f". Here's the message form the validator: {state['messages'][-1].content}"),
            ]
            response = llm.invoke(messages)
            question = json.loads(response.content)

            state["questions"][state["current_index"]] = question
            state["curr_question_valid"] = True
            return {"messages": AIMessage(f"regenerated question {state['current_index']}")}
        else:
            # generate all questions
            messages = [
                SystemMessage(prompt),
                HumanMessage(state["notes_summary"]),
            ]

            response = llm.invoke(messages)
            question = json.loads(response.content)
            state["questions"] = question
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

    return final_state["questions"]

if __name__ == "__main__":
    def get_notes():
        return "1 + 1 = 2"
    def get_syllabus():
        return "elementary math"

    questions = generate_questions(get_notes, get_syllabus)
