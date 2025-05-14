# utils/io.py

def format_io_pairs_as_python_list(pairs: list[tuple[str, str]]) -> str:
    """
    Formats input/output pairs as a valid Python list of tuples.
    """
    return "[" + ", ".join(f'({repr(i.strip())}, {repr(o.strip())})' for i, o in pairs) + "]"
