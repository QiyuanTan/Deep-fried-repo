from typing import TypedDict, Literal, Union, Annotated
from langgraph.graph import add_messages

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
    notes_summary: str
    curr_question_valid: bool
    messages: Annotated[list, add_messages]
    __next__: str