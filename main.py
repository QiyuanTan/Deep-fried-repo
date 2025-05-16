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

def generate_questions(notes, syllabus):

    graph_builder = StateGraph(State)

    def summarizer(state: State):
        # Summarize the question and context
        with open("prompts/summarizer_prompt.txt", "r") as f:
            prompt = f.read()

        messages = [
            SystemMessage(prompt),
            HumanMessage(f"Please generate {state['num_questions']} questions for me. \n"
                         f"Here's the syllabus of my course:\n{syllabus}. \n\n"
                         f"Here's my notes:\n{notes}"),
        ]

        response = llm.invoke(messages)

        state["notes_summary"] = response.content
        return state

    def generator(state: State):
        with open("prompts/quiz_generator.txt", "r", encoding='utf-8') as f:
            prompt = f.read()

        if not state["curr_question_valid"]:
            # regenerate a single question
            messages = [
                SystemMessage(prompt),
                HumanMessage(state["notes_summary"]),
                AIMessage(state["questions"]),
                SystemMessage(f"One of questions you generated is invalid. You need to regenerate it and format it as the following format:" # TODO: json format
                              f". Here's the message form the validator: {state['messages'][-1]}"),
            ]
            response = llm.invoke(messages)
            question = json.loads(response.content)

            state["questions"][state["current_index"]] = question
            state["curr_question_valid"] = True
            state["messages"] = state["messages"] + [f"regenerated question {state['current_index']}: {question}"]
            return state
        else:
            # generate all questions
            messages = [
                SystemMessage(prompt),
                HumanMessage(state["notes_summary"]),
            ]

            response = llm.invoke(messages)
            question = json.loads(response.content)
            state["questions"] = question["questions"]
            state["messages"] = state["messages"] + [f"generated questions: {question}"]
            return state

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
        "notes_summary": "",
        "curr_question_valid": True,
        "messages": [
        ]},
        {"recursion_limit": 1000})

    for message in final_state['messages']:
        print(message)

    return final_state["questions"]

if __name__ == "__main__":
    # notes = "lecture 1:\n 1 + 1 = 2 \n2 + 2 = 4\n3 + 3 = 6 addition is fun!"
    # syllabus = "Course on basic math\nTopics: addition, subtraction, multiplication, division\n"
    syllabus = "Recursion and Dynamic Programming\nTopics: Fibonacci sequence, factorial calculation, memoization\n"
    notes = "Lecture 1: Recursion basics\n- Fibonacci sequence\n- Factorial calculation\n- Memoization techniques\n\nLecture 2: Dynamic Programming\n- Coin change problem\n- Longest common subsequence\n- Knapsack problem\n"

    questions = generate_questions(notes, syllabus)

    print("Generated Questions:")
    for question in questions:
        print(question)