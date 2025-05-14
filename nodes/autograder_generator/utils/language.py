# utils/language.py

def detect_language(code: str) -> str:
    if "System.out.println" in code:
        return "java"
    elif "#include" in code:
        return "cpp"
    elif "console.log" in code:
        return "javascript"
    elif "def " in code or "print(" in code:
        return "python"
    return "python"  # Fallback
