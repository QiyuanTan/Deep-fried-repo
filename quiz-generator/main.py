# main.py

import os
from dotenv import load_dotenv
from state_types import State
from nodes.autograder import build_autograder_node

from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env
load_dotenv()

def main():
    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro-001",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Build autograder node
    autograder_node = build_autograder_node(llm)

    # Example mock state — replace with your test data
    state: State = {
        "questions": [
            {
                "title": "Add Two Numbers",
                "context": "Write a function that takes two integers as input and returns their sum.",
                "topics": ["functions", "basic arithmetic"],
                "question_type": "code",
                "sample_code": "def add_numbers(a, b):\n    return a + b",
                "autograder_script": "",
                "sample_input_output": [
                    ("1 2", "3"),
                    ("5 7", "12")
                ]
            }
        ],
        "num_questions": 1,
        "current_index": 0,
        "topics": [],
        "curr_question_valid": False,
        "messages": [],
        "__next__": ""
    }

    # Run only the autograder node
    updated_state = autograder_node.invoke(state)

    # Output result for debugging
    generated_script = updated_state["questions"][0]["autograder_script"]
    print("\n=== Generated Autograder Script ===\n")
    print(generated_script)

if __name__ == "__main__":
    main()
