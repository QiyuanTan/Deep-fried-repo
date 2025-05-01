import traceback
from typing import Tuple
from langchain_core.tools import tool

def validateMCQs(question: dict) -> Tuple[bool, str]:
    options = question.get("options", [])
    correct = question.get("correct_option", "")
    if not options:
        return False, "MCQ validation failed: No options provided."
    if correct not in options:
        return False, "MCQ validation failed: Correct option not in options list."
    return True, "MCQ validation passed."

def validateCode(question: dict) -> Tuple[bool, str]:
    script = question.get("autograder_script", "")
    samples = question.get("sample_input_output", [])

    try:
        # Syntax check
        compile(script, "<autograder>", "exec")
    except SyntaxError as e:
        return False, f"Syntax error in autograder script: {e}"

    for idx, (inp, expected) in enumerate(samples):
        try:
            local_scope = {}
            exec(script, {}, local_scope)
        except Exception as e:
            return False, f"Runtime error on sample {idx}: {traceback.format_exc()}"

        # Now validate each sample input-output pair
    for idx, (inp, expected) in enumerate(samples):
        # Try to get the function from the local scope (assumed to be defined in the script)
        func = local_scope.get('autograder_function')  # Change 'autograder_function' to the function name used in your script
        
        if func is None:
            return False, f"Function 'autograder_function' not found in the script."

        try:
            # Execute the function with the given input
            result = func(*inp)

            # Compare result with expected output
            if str(result) != str(expected):  # String comparison, assuming string output is expected
                return False, f"Test {idx} failed: Expected {expected}, but got {result}."
        
        except Exception as e:
            return False, f"Runtime error on sample {idx}: {traceback.format_exc()}"

    return True, "Code question validation passed."



@tool
def validator(state: dict) -> dict:
    index = state["current_index"]
    question = state["questions"][index]  # Get current question
    valid = False
    message = ""

    if question["question_type"] == "mcq":
        valid, message = validateMCQs(question)  # Validate MCQ
    elif question["question_type"] == "code":
        valid, message = validateCode(question)  # Validate Code question

    # Set the validity flag
    state["curr_question_valid"] = valid  # True or False based on validation

    # Determine next node based on the question's validity
    if valid and index + 1 == state["num_questions"]:  # Last question, valid
        state["__next__"] = "End"
    elif valid:  # Valid question, continue to the autograder
        state["__next__"] = "Autograder"
    else:  # Invalid question, regenerate the question
        state["__next__"] = "Generator"

    # Add validation message for logging/debugging
    state["messages"].append(f"Question {index} validation result: {message}")

    return state
