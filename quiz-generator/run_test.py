# run_test.py

import os
import sys
from dotenv import load_dotenv
from state_types import State
from nodes.autograder import build_autograder_node
from tests.test_autograder import run_autograder_script
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env
load_dotenv()

def generate_autograder_script(question_data):
    """
    Generates an autograder script for the given question data
    
    Args:
        question_data (dict): Question data containing title, context, sample_code, etc.
        
    Returns:
        str: The generated autograder script
    """
    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro-001",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Build autograder node
    autograder_node = build_autograder_node(llm)

    # Create a state with the question
    state: State = {
        "questions": [question_data],
        "num_questions": 1,
        "current_index": 0,
        "topics": [],
        "curr_question_valid": False,
        "messages": [],
        "__next__": ""
    }

    # Run only the autograder node
    updated_state = autograder_node.invoke(state)
    return updated_state["questions"][0]["autograder_script"]

def test_autograder_with_submissions():
    """Tests the autograder scripts with different code submissions across various questions"""
    
    # Define test questions (each with different types of challenges)
    test_questions = [
        # Question 1: Basic addition
        {
            "title": "Add Two Numbers",
            "context": "Write a function that takes two integers as input and returns their sum.",
            "topics": ["functions", "basic arithmetic"],
            "question_type": "code",
            "sample_code": "def add_numbers(a, b):\n    return a + b",
            "autograder_script": "",
            "sample_input_output": [
                ("1 2", "3"),
                ("5 7", "12"),
                ("-3 8", "5")
            ]
        },
        # Question 2: String manipulation
        {
            "title": "Reverse String",
            "context": "Write a function that takes a string as input and returns it reversed.",
            "topics": ["strings", "algorithms"],
            "question_type": "code",
            "sample_code": "def reverse_string(text):\n    return text[::-1]",
            "autograder_script": "",
            "sample_input_output": [
                ("hello", "olleh"),
                ("python", "nohtyp"),
                ("", ""),
                ("a", "a")
            ]
        },
        # Question 3: List processing 
        {
            "title": "Find Maximum",
            "context": "Write a function that finds the maximum value in a list of integers.",
            "topics": ["lists", "algorithms"],
            "question_type": "code",
            "sample_code": "def find_max(numbers):\n    return max(numbers)",
            "autograder_script": "",
            "sample_input_output": [
                ("1 5 3 9 2", "9"),
                ("-5 -2 -10", "-2"),
                ("42", "42")
            ]
        }
    ]
    
    # For each test question, generate an autograder and test with submissions
    for i, question in enumerate(test_questions):
        print(f"\n\n{'='*60}")
        print(f"TESTING QUESTION {i+1}: {question['title']}")
        print(f"{'='*60}")
        
        # Generate autograder script for this question
        print(f"Generating autograder script...")
        autograder_script = generate_autograder_script(question)
        print(f"Autograder script generated!")
        
        # Define test submissions for this specific question type
        test_submissions = []
        
        if question["title"] == "Add Two Numbers":
            test_submissions = [
                {
                    "description": "Correct solution (function implementation)",
                    "code": """def add_numbers(a, b):
    return a + b

# Parse input and call function
if __name__ == "__main__":
    a, b = map(int, input().split())
    print(add_numbers(a, b))
""",
                    "expected": True
                },
                {
                    "description": "Correct solution (direct implementation)",
                    "code": """a, b = map(int, input().split())
print(a + b)
""",
                    "expected": True
                },
                {
                    "description": "Incorrect solution (subtracts instead of adds)",
                    "code": """a, b = map(int, input().split())
print(a - b)
""",
                    "expected": False
                }
            ]
        elif question["title"] == "Reverse String":
            test_submissions = [
                {
                    "description": "Correct solution using slicing",
                    # Add a newline character at the end to simulate pressing Enter after input
                    "code": """text = input().strip()
print(text[::-1])
""",
                    "expected": True
                },
                {
                    "description": "Correct solution using loops",
                    "code": """text = input().strip()
reversed_text = ""
for char in text:
    reversed_text = char + reversed_text
print(reversed_text)
""",
                    "expected": True
                },
                {
                    "description": "Incorrect solution (doesn't reverse)",
                    "code": """text = input().strip()
print(text)
""",
                    "expected": False
                }
            ]
        elif question["title"] == "Find Maximum":
            test_submissions = [
                {
                    "description": "Correct solution using max()",
                    "code": """numbers = list(map(int, input().split()))
print(max(numbers))
""",
                    "expected": True
                },
                {
                    "description": "Correct solution using loops",
                    "code": """numbers = list(map(int, input().split()))
max_value = numbers[0]
for num in numbers[1:]:
    if num > max_value:
        max_value = num
print(max_value)
""",
                    "expected": True
                },
                {
                    "description": "Incorrect solution (returns min instead of max)",
                    "code": """numbers = list(map(int, input().split()))
print(min(numbers))
""",
                    "expected": False
                }
            ]
        
        # Run each test submission and report results
        print(f"\n----- TESTING WITH DIFFERENT USER SUBMISSIONS -----")
        for submission in test_submissions:
            print(f"\nTest: {submission['description']}")
            print(f"Code:\n{submission['code']}")
            
            # Create a custom test function for the Reverse String problem
            if question["title"] == "Reverse String" and submission["expected"]:
                # Manual check for the string reversal solutions to debug the issue
                print("Testing with manual string checks...")
                try:
                    result = run_autograder_script(autograder_script, submission['code'])
                    
                    # Clearer test status reporting
                    test_passed = result == submission['expected']
                    submission_passed = result  # Did the submitted code pass the autograder?
                    
                    if test_passed:
                        if submission_passed:
                            status_msg = "✓ TEST PASSED: Correct solution was accepted"
                        else:
                            status_msg = "✓ TEST PASSED: Incorrect solution was rejected"
                    else:
                        if submission_passed:
                            status_msg = "✗ TEST FAILED: Incorrect solution was accepted"
                        else:
                            status_msg = "✗ TEST FAILED: Correct solution was rejected"
                    
                    print(f"Result: {status_msg}")
                    print(f"- Autograder returned: {result} (Expected: {submission['expected']})")
                    
                    if not result and submission['expected']:
                        print("Debugging input handling...")
                        print(f"Test inputs: {[input_data for input_data, _ in question['sample_input_output']]}")
                except Exception as e:
                    print(f"Error running test: {e}")
            else:
                # Normal test execution with improved status reporting
                result = run_autograder_script(autograder_script, submission['code'])
                
                # Clearer test status reporting
                test_passed = result == submission['expected']
                submission_passed = result  # Did the submitted code pass the autograder?
                
                if test_passed:
                    if submission_passed:
                        status_msg = "✓ TEST PASSED: Correct solution was accepted"
                    else:
                        status_msg = "✓ TEST PASSED: Incorrect solution was rejected"
                else:
                    if submission_passed:
                        status_msg = "✗ TEST FAILED: Incorrect solution was accepted"
                    else:
                        status_msg = "✗ TEST FAILED: Correct solution was rejected"
                
                print(f"Result: {status_msg}")
                print(f"- Autograder returned: {result} (Expected: {submission['expected']})")
    
    print("\n===== ALL TESTING COMPLETE =====")

if __name__ == "__main__":
    test_autograder_with_submissions()