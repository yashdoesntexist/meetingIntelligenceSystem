from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict
import csv


@dataclass
class Utterance:
    speaker: str
    text: str


@dataclass
class Meeting:
    name: str
    utterances: List[Utterance]
    roles: Dict[str, str]


def load_roles(roles_path: Path) -> Dict[str, str]:
    roles: Dict[str, str] = {}
    if not roles_path.exists():
        return roles

    with roles_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            spk = row.get("speaker") or row.get("id") or row.get("name")
            role = row.get("role") or ""
            if spk:
                roles[spk.strip()] = role.strip()
    return roles


def load_meeting(transcript_path: Path, roles_path: Path) -> Meeting:
    """
    Load a meeting from a simple transcript file:
    Each line: SPEAKER: text
    If no colon, speaker defaults to UNK.
    """
    utterances: List[Utterance] = []
    with transcript_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                spk, txt = line.split(":", 1)
                speaker = spk.strip() or "UNK"
                text = txt.strip()
            else:
                speaker = "UNK"
                text = line
            if text:
                utterances.append(Utterance(speaker=speaker, text=text))

    roles = load_roles(roles_path)
    return Meeting(
        name=transcript_path.stem,
        utterances=utterances,
        roles=roles,
    )
