

def load_transcript(filepath: str) -> str:
    """Load raw transcript text from a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
