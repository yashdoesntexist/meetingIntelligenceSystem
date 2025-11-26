from pathlib import Path
from typing import Iterable


def iter_meeting_files(input_dir: Path) -> Iterable[Path]:
    """
    Yield all transcript .txt files in input_dir, skipping roles.csv.
    """
    for p in sorted(input_dir.glob("*.txt")):
        if p.name.lower() == "roles.csv":
            continue
        yield p
