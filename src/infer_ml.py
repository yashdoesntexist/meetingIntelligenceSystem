from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import typer
import joblib
from rich import print

from config import RAW_DIR, DEFAULT_OUTPUT_JSON, DEFAULT_MODEL_PATH
from ami_loader import load_meeting, Utterance
from action_rules import extract_task_and_deadline
from temporal import normalize_deadline
from coref_simple import resolve_pronouns
from utils import iter_meeting_files

app = typer.Typer()

MIN_TASK_WORDS = 4  # simple quality filter


def choose_assignee(
    utt: Utterance,
    roles: dict[str, str],
    parsed: dict,
    last_addr: Optional[str],
) -> tuple[str, str]:
    """
    Simple heuristic to choose who owns the action.
    """
    # Name explicitly extracted by the rules
    if parsed.get("assignee_name"):
        nm = parsed["assignee_name"]
        if nm in roles.keys():
            return nm, roles.get(nm, "")
        return nm, ""

    # Fallback to pronoun resolution
    pron = resolve_pronouns(utt.text, utt.speaker, last_addr)
    if pron["i"]:
        return utt.speaker, roles.get(utt.speaker, "")
    if pron["you"] and pron["you"] in roles:
        return pron["you"], roles.get(pron["you"], "")

    # Default: speaker owns it
    return utt.speaker, roles.get(utt.speaker, "")


@app.command()
def main(
    input_dir: str = typer.Option(str(RAW_DIR), "--input-dir", "--input_dir"),
    model_path: str = typer.Option(str(DEFAULT_MODEL_PATH), "--model-path", "--model_path"),
    out_json: str = typer.Option(str(DEFAULT_OUTPUT_JSON), "--out-json", "--out_json"),
):
    # Try to load the classifier, else fall back to rules only
    try:
        clf = joblib.load(model_path)
        print(f"[green]Loaded ML model -> {model_path}")
    except Exception as e:
        clf = None
        print(f"[yellow]Model not loaded ({e}). Falling back to rules only.")

    results: list[dict] = []

    for p in iter_meeting_files(Path(input_dir)):
        meeting = load_meeting(p, Path(input_dir) / "roles.csv")
        last_addressed: Optional[str] = None

        for utt in meeting.utterances:
            text = utt.text.strip()
            if not text:
                continue

            # 1) Decide if this utterance is an action
            if clf is not None:

                try:
                    proba = clf.predict_proba([text])[0][1]
                    # a slightly lower threshold keeps recall reasonable
                    is_action = proba >= 0.40
                except Exception:
                    is_action = bool(extract_task_and_deadline(text))
            else:
                is_action = bool(extract_task_and_deadline(text))

            if not is_action:
                continue

            # 2) Parse out task and deadline (rules)
            parsed = extract_task_and_deadline(text)
            if not parsed:
                parsed = {
                    "task": text,
                    "deadline_raw": None,
                    "assignee_name": None,
                }

            task = (parsed.get("task") or "").strip()
            if not task:
                continue

            # simple quality filter – avoid very short fragments
            if len(task.split()) < MIN_TASK_WORDS:
                continue

            # 3) Assignee + role
            assignee, role = choose_assignee(utt, meeting.roles, parsed, last_addressed)

            # 4) Deadline – keep only text in output, still normalize internally if needed
            deadline_text = parsed.get("deadline_raw")
            if deadline_text:
                _ = normalize_deadline(deadline_text, ref=datetime.now())
                # we ignore the ISO value in the JSON on purpose

            # 5) Track last addressed name (for “you” resolution)
            toks = text.split()
            if toks and toks[0].rstrip(",").isalpha() and toks[0].istitle():
                last_addressed = toks[0].rstrip(",")

            # 6) Store result – NO deadline_iso in output
            results.append(
                {
                    "meeting": meeting.name,
                    "speaker": utt.speaker,
                    "speaker_role": meeting.roles.get(utt.speaker, ""),
                    "assignee": assignee,
                    "assignee_role": role,
                    "action_item": task,
                    "deadline_text": deadline_text,
                }
            )

    Path(out_json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[green]Wrote {len(results)} actions (ML+rules) -> {out_json}")


if __name__ == "__main__":
    app()
