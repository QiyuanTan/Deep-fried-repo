# nodes/autograder.py

from typing import Callable
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
import re

from state_types import State
from utils.language import detect_language
from utils.io import format_io_pairs_as_python_list
from utils.llm import extract_code
from utils.state import get_current_question, set_current_question


# Load prompt from text file
with open("prompts/autograder_prompt.txt", "r") as f:
    autograder_prompt = ChatPromptTemplate.from_template(f.read())


def build_autograder_node(llm: BaseChatModel) -> RunnableLambda:
    def autograder_step(state: State) -> State:
        index = state["current_index"]
        question = state["questions"][index]

        if question["question_type"] != "code":
            return state  # Skip MCQs

        # 1. Detect programming language and extension
        lang = detect_language(question["sample_code"])
        ext = {
            "python": "py",
            "cpp": "cpp",
            "java": "java",
            "c": "c",
            "javascript": "js"
        }.get(lang, "txt")

        # 2. Prepare inputs
        from utils.io import format_io_pairs_as_python_list

        input_values = {
            "language": lang,
            "ext": ext,
            "title": question["title"],
            "context": question["context"],
            "sample_code": question["sample_code"],
            "formatted_io": format_io_pairs_as_python_list(question["sample_input_output"])
        }

        # 3. Run the chain (Prompt | LLM)
        response = (autograder_prompt | llm).invoke(input_values)

        # 4. Clean up the response to extract Python code
        autograder_script = extract_code(response.content)
        
        # 5. Ensure all template variables are properly replaced
        # This is needed because the LLM might not properly substitute the variables
        for key, value in input_values.items():
            pattern = r'\{\{' + key + r'\}\}'  # Match {{key}}
            autograder_script = re.sub(pattern, str(value), autograder_script)
            
            # Also replace any {key} format that might remain
            pattern = r'\{' + key + r'\}'  # Match {key}
            autograder_script = re.sub(pattern, str(value), autograder_script)

        # 6. Save to state
        question["autograder_script"] = autograder_script
        state["questions"][index] = question

        return state

    return RunnableLambda(autograder_step)
