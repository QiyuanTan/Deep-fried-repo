import random
from typing import TypedDict, Annotated, Union, Literal

from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_community.tools.tavily_search.tool import TavilySearchResults

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import os

from langgraph.constants import START, END
from langgraph.graph import add_messages, StateGraph

class Question(TypedDict):
    title: str
    context: str
    topics: list[str]
    question_type: Literal["mcq", "code"]

class MCQ(Question):
    options: list[str]
    correct_option: str

class CodeQuestion(Question):
    sample_code: str
    autograder_script: str
    sample_input_output: list[tuple[str, str]]

class State(TypedDict):
    questions: list[Union[MCQ, CodeQuestion]]
    num_questions: int
    current_index: int
    topics: list[str]
    curr_question_valid: bool
    messages: Annotated[list, add_messages]
    __next__: str

graph_builder = StateGraph(State)

def summarizer(state: State):
    state["topics"] = ["topic1", "topic2"]
    return {"messages": AIMessage("some additional comments about the topics")}

def generator(state: State):
    if not state["curr_question_valid"]:
        # regenerate the question
        state["questions"][state["current_index"]] = {
            "title": "New Question",
            "context": "New Context",
            "topics": ["topic1", "topic2"],
            "question_type": "mcq",
            "options": ["Option A", "Option B"],
            "correct_option": "Option A"
        }

        state["curr_question_valid"] = True
        return {"messages": AIMessage(f"regenerated question {state['current_index']}")}
    else:
        # generate all questions
        for i in range(state["num_questions"]):
            state["questions"].append({
                "title": f"Question {i}",
                "context": f"Context for question {i}",
                "topics": state["topics"],
                "question_type": "mcq",
                "options": ["Option A", "Option B"],
                "correct_option": "Option A"
            })

        state["questions"].append({
            "title": f"Question ",
            "context": f"Context for question",
            "topics": state["topics"],
            "question_type": "code",
            "sample_code": "print('Hello World')",
            "autograder_script": "",
            "sample_input_output": []
        })
        return {"messages": AIMessage("generated all questions")}

def autograder_generator(state: State):
    if state["questions"][state["current_index"]]["question_type"] == "code":
        question: CodeQuestion = state["questions"][state["current_index"]]
        question["autograder_script"] = "autograder script"
        question["sample_input_output"] = [("input", "output"), ("input", "output")]
        return {"messages": AIMessage(f"generated autograder for question {state['current_index']}")}
    else:
        return {"messages": AIMessage(f"no autograder needed for question {state['current_index']}")}

def validator(state: State):
    # question = state["questions"][state["current_index"]]
    # if question["question_type"] == "mcq":
    #     state["curr_question_valid"] = True
    # elif question["question_type"] == "code":
    #     state["curr_question_valid"] = True
    # else:
    #     state["curr_question_valid"] = False
    state["curr_question_valid"] = random.random() > 0.5
    if not state["curr_question_valid"]:
        state["__next__"] = "generator"
    else:
        state["__next__"] = "autograder_generator"
        state["current_index"] = state["current_index"] + 1
    if not state["current_index"] < len(state["questions"]):
        state["__next__"] = END

    state["messages"].append(AIMessage(content=f"validated question {state['current_index'] - (1 if state['curr_question_valid'] else 0)}, valid: {state['curr_question_valid']}"))

    return state

graph_builder.add_node("summarizer", summarizer)
graph_builder.add_node("generator", generator)
graph_builder.add_node("autograder_generator", autograder_generator)
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
    "topics": ["topic1", "topic2"],
    "curr_question_valid": True,
    "messages": [
    ]},
    {"recursion_limit": 1000})
for message in final_state['messages']:
    print(message.content)