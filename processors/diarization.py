
import re

def identify_speakers(text: str):
    """
    Very simple rule-based speaker detection.
    Detects lines starting with 'Name:' patterns.
    """
    lines = text.split("\n")
    structured = []

    current_speaker = "Unknown"

    for line in lines:
        line = line.strip()

        # Detect names like: "John:" or "Sarah - "
        speaker_match = re.match(r"^([A-Za-z]+)[\:\-]\s*(.*)", line)
        if speaker_match:
            current_speaker = speaker_match.group(1)
            content = speaker_match.group(2)
        else:
            content = line

        if content:
            structured.append({"speaker": current_speaker, "text": content})

    return structured
