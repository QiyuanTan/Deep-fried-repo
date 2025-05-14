from typing import TypedDict, Literal, Union, Annotated

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
    notes_summary: list[str]
    curr_question_valid: bool
    messages: Annotated[list, lambda x: x]  # Replace with actual logic
    __next__: str
