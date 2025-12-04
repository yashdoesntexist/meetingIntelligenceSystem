from __future__ import annotations
import re
from typing import Optional, Dict

# Phrases that usually start an action or request

CLEAN_TRIGGERS = [
    "we need to",
    "we should",
    "can you",
    "could you",
    "please",
    "let's all",
    "let's",
    "let us",
    "i think we should",
    "i will",
    "you need to",
    "you should",
    "can we",
    "shall we",
]


DEADLINE_PATTERNS = [
    # by Friday, by next week, by end of day
    re.compile(r"\bby ([^,.!?]+)", re.IGNORECASE),
    # in the next two days, in the next 3 weeks
    re.compile(r"\bin the next ([^,.!?]+)", re.IGNORECASE),
    # within 2 days, within a week
    re.compile(r"\bwithin ([^,.!?]+)", re.IGNORECASE),
    # next Tuesday, next meeting, tomorrow, today
    re.compile(r"\b(next [^,.!?]+|tomorrow|today|tonight)\b", re.IGNORECASE),
]



def _extract_assignee_name(text: str) -> Optional[str]:
    """
    Try to guess the assignee name from simple patterns like:
      "Jason, can you ..."
      "Sue can you ..."
      "Can you, Jason, ..."
      "Oh can you put a sign up on all the spaces Jason?"
    We just return a single capitalized first name.
    """
    # Name, can you ...
    m = re.search(r"\b([A-Z][a-z]+)\b,\s*can you", text)
    if m:
        return m.group(1)

    # Name can you ...
    m = re.search(r"\b([A-Z][a-z]+)\b\s+can you", text)
    if m:
        return m.group(1)

    # Can you, Name, ...
    m = re.search(r"can you,?\s+([A-Z][a-z]+)\b", text)
    if m:
        return m.group(1)

    # Name, please ...
    m = re.search(r"\b([A-Z][a-z]+)\b,\s*please", text)
    if m:
        return m.group(1)

    # Leading "Name," at the beginning of the sentence
    m = re.match(r"^([A-Z][a-z]+),", text.strip())
    if m:
        return m.group(1)

    return None



def extract_task_and_deadline(text: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Rule-based extraction of:
      - task (cleaned to start from an action trigger)
      - deadline_raw (string like "in the next two days")
      - assignee_name (simple first name if we can find it)

    Returns None if we do NOT see any obvious action trigger.
    """

    if not text or not text.strip():
        return None

    original = text.strip()
    lower = original.lower()

    # 1) Detect if this sentence even looks like an action
    trigger_idx = None
    for trig in CLEAN_TRIGGERS:
        idx = lower.find(trig)
        if idx != -1:
            if trigger_idx is None or idx < trigger_idx:
                trigger_idx = idx

    if trigger_idx is None:
        # No action-like phrase -> treat as non-action
        return None

    # 2) Task text: start from the first trigger
    task = original[trigger_idx:].strip()

    # Optionally, cut at the first sentence boundary after the trigger
    # to avoid dragging too much junk at the end.
    end_match = re.search(r"[.?!]", task)
    if end_match and end_match.end() < len(task):
        # keep up to first . ? ! and drop the rest
        task = task[: end_match.end()].strip()

    # 3) Extract deadline (if any) from the original full text
    deadline_raw: Optional[str] = None
    for pat in DEADLINE_PATTERNS:
        m = pat.search(original)
        if m:
            # use the full matched phrase or group(0)
            deadline_raw = m.group(0).strip()
            break

    # 4) Extract assignee name (if any)
    assignee_name = _extract_assignee_name(original)

    # 5) Final sanity check: require at least a few words in the task
    if len(task.split()) < 3:
        # too short, likely garbage
        return None

    return {
        "task": task,
        "deadline_raw": deadline_raw,
        "assignee_name": assignee_name,
    }
