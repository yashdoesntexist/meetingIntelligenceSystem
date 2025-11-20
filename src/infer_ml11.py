from __future__ import annotations
import json
from pathlib import Path

import typer
from rich import print

from config import RAW_DIR, DEFAULT_OUTPUT_JSON
from ami_loader import load_meeting, Utterance
from action_rules import extract_task_and_deadline
from utils import iter_meeting_files

# Verbs that usually mark a concrete action
ACTION_VERBS = {
    "send", "email", "share", "prepare", "update", "review", "finish",
    "complete", "report", "present", "schedule", "arrange", "organize",
    "follow", "follow-up", "call", "book", "draft", "finalize",
    "deliver", "submit", "assign", "decide", "agree", "explain",
    "refer", "address", "take", "put", "come", "wash", "pay",
    "clean", "respond", "reply", "check", "confirm", "think",
}

# Phrases that are just meeting navigation or fluff
BAD_START_PATTERNS = [
    "we should get started",
    "let's get started",
    "lets get started",
    "let's get the ball rolling",
    "lets get the ball rolling",
    "let's move on to the next topic",
    "lets move on to the next topic",
    "let's move on to the next item",
    "lets move on to the next item",
    "let's move on to the next",
    "lets move on to the next",
    "let's move on",
    "lets move on",
    "let's start",
    "lets start",
    "let's take a look at",
    "lets take a look at",
    "let's make this the next red bull energy drink",
]

# Tasks ending with only these are usually incomplete
BAD_END_WORDS = {
    "for", "to", "of", "about", "at", "on", "up", "with",
    "letting", "than", "upcoming", "issue", "background", "again",
}

# Substrings that often produce junk actions
BAD_SUBSTRINGS = [
    "come and get back",                  # nonsense fragment
    "you should because you ride your bike",  # joke, not a real task
]

QUESTION_STARTS = [
    "what", "why", "how", "who", "where", "when",
]

MIN_WORDS = 4

LEADING_FILLERS = [
    "okay",
    "ok",
    "well",
    "so",
    "right",
    "alright",
    "now",
    "fine",
]

REQUEST_PREFIXES = [
    "can you",
    "could you",
    "will you",
    "would you",
    "please can you",
    "please could you",
    "please will you",
    "please would you",
    "i think we should",
    "i think we need to",
    "we should",
    "we need to",
    "we ought to",
    "let's",
    "lets",
    "i will",
    "i'll",
    "we will",
    "we'll",
    "can we",
    "could we",
    "shall we",
    "should we",
    "let us",
    "i am going to",
    "we are going to",
    "i'm gonna",
    "we're gonna",
    "i am planning to",
    "we are planning to",
    "i intend to",
    "we intend to",
    "i was wondering if you could",
    "would it be possible to",
    "is there any chance you could",
    "i need you to",
    "we need you to",
    "i want you to",
    "we want you to",
    "id like you to",
    "wed like you to",
    "yo can you",
    "hey can you",
    "bro can you",
    "man can you",
    "listen can you",
    "ok can you",
    "hey let's",
    "ok let's",

]


def clean_task_phrase(task: str) -> str:
    """
    Clean the raw task phrase:
    - remove navigation sentence before first '.' if it matches BAD_START_PATTERNS
    - drop fillers (okay, well, so, etc.)
    - strip polite wrappers (can you, can we, we should, let's, I will, etc.)
    """
    if not task:
        return ""

    t = task.strip()
    lower = t.lower()

    # Remove leading navigation clause like "we should get started."
    for bad in BAD_START_PATTERNS:
        if lower.startswith(bad):
            dot_idx = t.find(".")
            if dot_idx != -1 and dot_idx + 1 < len(t):
                t = t[dot_idx + 1 :].lstrip()
                lower = t.lower()
            else:
                # whole thing is just navigation
                return ""
            break

    # Drop leading filler words (okay, well, so, etc.)
    changed = True
    while changed:
        changed = False
        for f in LEADING_FILLERS:
            prefix = f + " "
            if lower.startswith(prefix):
                t = t[len(prefix) :].lstrip()
                lower = t.lower()
                changed = True
                break

    # Remove polite request wrappers at very front
    for pref in REQUEST_PREFIXES:
        prefix = pref + " "
        if lower.startswith(prefix):
            candidate = t[len(prefix) :].lstrip()
            # Only accept if at least 2 words remain
            if len(candidate.split()) >= 2:
                t = candidate
                lower = t.lower()
            else:
                return ""
            break

    return t


def is_strict_action(task: str, original: str) -> bool:
    """
    Ultra-strict filter: keep only sentences that really look like action items.
    """
    if not task:
        return False

    t = task.strip()
    lower = t.lower()
    original_q = original.strip().endswith("?")

    # Kill obvious junk fragments
    for bad_sub in BAD_SUBSTRINGS:
        if bad_sub in lower:
            return False

    words = [w.strip(".,?!") for w in t.split()]
    lower_words = [w.lower() for w in words if w]

    # Minimum length
    if len(lower_words) < MIN_WORDS:
        return False

    # Drop obvious meeting navigation or fluff at start
    for bad in BAD_START_PATTERNS:
        if lower.startswith(bad):
            return False

    # Drop pure questions starting with wh- words
    if lower_words[0] in QUESTION_STARTS:
        return False

    # Require at least one strong action verb or modal
    has_action_verb = any(
        w in ACTION_VERBS or w in {"need", "should", "must"} for w in lower_words
    )
    if not has_action_verb:
        return False

    # Extra rule for sentences that were questions in the original text
    if original_q:
        # We only keep question-shaped sentences that are effectively imperatives
        # e.g. "put a sign up on all the spaces Jason?" or "explain the background to this?"
        first = lower_words[0]
        imperative_leading = (
            first in ACTION_VERBS
            or first == "please"
            or (first == "all" and len(lower_words) > 1 and lower_words[1] in ACTION_VERBS)
        )
        if not imperative_leading:
            return False

    # If it ends with an obviously incomplete trailing word, drop
    if lower_words[-1] in BAD_END_WORDS:
        return False

    return True


# ----------------------------------------------------------
# MAIN EXTRACTION — RULES ONLY + REAL DEADLINES (NO ISO)
# ----------------------------------------------------------

app = typer.Typer()


@app.command()
def main(
    input_dir: str = typer.Option(str(RAW_DIR), "--input-dir", "--input_dir"),
    out_json: str = typer.Option(str(DEFAULT_OUTPUT_JSON), "--out-json", "--out_json"),
):
    """
    Iterate over AMI-style transcripts in input_dir, detect action items
    using ultra-strict rule-based logic, and write them to out_json.

    Output format (per action):
      {
        "meeting": "<file-stem>",
        "speaker": "<speaker-id or UNK>",
        "action_item": "<cleaned action text>",
        "deadline": "<deadline phrase or null>"
      }
    """

    results = []

    for p in iter_meeting_files(Path(input_dir)):
        meeting = load_meeting(p, Path(input_dir) / "roles.csv")

        for utt in meeting.utterances:
            text = (utt.text or "").strip()
            if not text:
                continue

            # Step 1: rule engine checks if this utterance has an action pattern
            parsed = extract_task_and_deadline(text)
            if not parsed:
                continue

            raw_task = (parsed.get("task") or "").strip()
            if not raw_task:
                continue

            # Step 2: clean the task phrase
            task = clean_task_phrase(raw_task)
            if not task:
                continue

            # Step 3: apply ultra-strict filter
            if not is_strict_action(task, text):
                continue

            # Step 4: deadline (raw phrase only, no ISO)
            deadline_raw = parsed.get("deadline_raw") or None

            results.append(
                {
                    "meeting": meeting.name,
                    "speaker": utt.speaker,
                    "action_item": task,
                    "deadline": deadline_raw,
                }
            )

    Path(out_json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[green]Wrote {len(results)} strict actions -> {out_json}")


if __name__ == "__main__":
    app()
