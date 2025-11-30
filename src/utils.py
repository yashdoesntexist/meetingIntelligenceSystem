from pathlib import Path
from typing import Iterable

#Utility Functions for Data Processing
#Author: Meriem Lmoubariki
#Common functions for text cleaning, I/O, and formatting

def iter_meeting_files(input_dir: Path) -> Iterable[Path]:
    """
    Yield all transcript .txt files in input_dir, skipping roles.csv.
    """
    for p in sorted(input_dir.glob("*.txt")):
        if p.name.lower() == "roles.csv":
            continue
        yield p
# Updated 
# Updated 
# Updated 
