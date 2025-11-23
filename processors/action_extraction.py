

import re
from models.patterns import ACTION_KEYWORDS

def extract_actions(structured_dialogue):
    action_items = []

    for entry in structured_dialogue:
        speaker = entry["speaker"]
        sentence = entry["text"]

        lowered = sentence.lower()

        if any(keyword in lowered for keyword in ACTION_KEYWORDS):
            action_items.append({
                "speaker": speaker,
                "action_item": sentence,
                "assignee": guess_assignee(sentence),
                "deadline": extract_deadline(sentence)
            })

    return action_items


def guess_assignee(sentence: str):
    """
    Naive MVP: detect 'you', 'John', etc.
    """
    you_match = re.search(r"\byou\b", sentence, re.IGNORECASE)
    if you_match:
        return "Someone_else"

    name_match = re.search(r"\b[A-Z][a-z]+\b", sentence)
    if name_match:
        return name_match.group(0)

    return "Unknown"


def extract_deadline(sentence: str):
    """
    Simple rule-based deadline extraction (MVP requirement).
    """
    deadline_match = re.search(r"by ([A-Za-z0-9 ]+)", sentence.lower())
    return deadline_match.group(1) if deadline_match else None
