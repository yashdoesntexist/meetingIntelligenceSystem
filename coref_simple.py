from __future__ import annotations
from typing import Optional

def resolve_pronouns(text: str, speaker: str, last_addressed: Optional[str]) -> dict:
    s = f" {text} ".lower()
    i_subject = speaker if (" i " in s or s.strip().startswith("i ")) else None
    you_subject = last_addressed if (" you " in s or s.strip().startswith("you ")) else None
    return {"i": i_subject, "you": you_subject}
