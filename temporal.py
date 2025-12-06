from __future__ import annotations
from datetime import datetime
from typing import Optional

import dateparser


def normalize_deadline(raw: Optional[str], ref: datetime) -> Optional[str]:
    """
    Convert vague deadlines like 'Friday', 'next week', 'tomorrow'
    into ISO date strings (YYYY-MM-DD) relative to ref.
    """
    if not raw:
        return None

    dt = dateparser.parse(
        raw,
        settings={
            "RELATIVE_BASE": ref,
            "PREFER_DATES_FROM": "future",
        },
    )
    if not dt:
        return None
    return dt.date().isoformat()
