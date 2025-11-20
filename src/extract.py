from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd
import typer
from rich import print


 # in this file i had to use utt roles and the parsed for the firt fucntion 
 
from config import RAW_DIR, DEFAULT_OUTPUT_JSON, PROCESSED_DIR
from ami_loader import load_meeting, Utterance
from action_rules import extract_task_and_deadline
from temporal import normalize_deadline
from coref_simple import resolve_pronouns
from utils import iter_meeting_files

app = typer.Typer()

def choose_assignee(utt: Utterance, roles: dict[str, str], parsed: dict, last_addr: Optional[str]) -> tuple[str, str]:
    if parsed.get("assignee_name"):
        nm = parsed["assignee_name"]
        if nm in roles.keys():
            return nm, roles.get(nm, "")
        return nm, ""
    pron = resolve_pronouns(utt.text, utt.speaker, last_addr)
    if pron["i"]:
        return utt.speaker, roles.get(utt.speaker, "")
    if pron["you"] and pron["you"] in roles:
        return pron["you"], roles.get(pron["you"], "")
    return utt.speaker, roles.get(utt.speaker, "")


@app.command()
def main(
    input_dir: str = typer.Option(str(RAW_DIR), "--input-dir", "--input_dir"),
    out_json: str = typer.Option(str(DEFAULT_OUTPUT_JSON), "--out-json", "--out_json")
):

    input_path = Path(input_dir)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for p in iter_meeting_files(input_path):
        meeting = load_meeting(p, Path(input_dir) / "roles.csv")
        last_addressed: Optional[str] = None
        for utt in meeting.utterances:
            parsed = extract_task_and_deadline(utt.text)
            if not parsed:
                continue
            assignee, role = choose_assignee(utt, meeting.roles, parsed, last_addressed)
            deadline_iso = normalize_deadline(parsed.get("deadline_raw"), ref=datetime.now())
            toks = utt.text.split()
            if toks and toks[0].rstrip(",").isalpha() and toks[0].istitle():
                last_addressed = toks[0].rstrip(",")
            results.append({
                "meeting": meeting.name,
                "speaker": utt.speaker,
                "speaker_role": meeting.roles.get(utt.speaker, ""),
                "assignee": assignee,
                "assignee_role": role,
                "action_item": parsed.get("task") or "",
                "deadline_text": parsed.get("deadline_raw"),
                "deadline_iso": deadline_iso
            })
    Path(out_json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[green]Wrote {len(results)} actions -> {out_json}")

if __name__ == "__main__":
    app()
