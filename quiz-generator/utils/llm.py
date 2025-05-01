# utils/llm.py

def extract_code(response: str) -> str:
    """
    Extracts code blocks from LLM responses.
    Looks for code between triple backticks (```) and returns just the code.
    If no triple backticks are found, returns the entire response (stripped).
    
    For autograder scripts, ensures any remaining template variables are preserved.
    """
    if "```" in response:
        # Find content between first pair of ``` markers
        parts = response.split("```")
        if len(parts) >= 3:  # At least one complete code block
            # Extract code from the first complete block, typically after 'python' language marker
            code_block = parts[1]
            # Remove language marker if present (like 'python')
            if code_block.strip() and '\n' in code_block:
                first_line = code_block.split('\n', 1)[0].strip()
                if not first_line.startswith("import") and not first_line.startswith("def") and not first_line.startswith("#"):
                    code_block = code_block.split('\n', 1)[1]
            return code_block.strip()
    
    return response.strip()
