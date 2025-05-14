# utils/state.py

def get_current_question(state: dict) -> dict:
    return state["questions"][state["current_index"]]

def set_current_question(state: dict, question: dict) -> None:
    state["questions"][state["current_index"]] = question
