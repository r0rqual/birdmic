#!/usr/bin/env python3
"""Print an eBird species frequency for a date from BirdMic frequency JSON.

Usage:
    python3 scripts/check_rare_bird.py SPECIES_CODE FREQUENCIES.json [YYYY-MM-DD]

The exit status is always zero for a successful lookup. A missing species is
reported as 1.0 (common/unknown), which is a safe default for alert workflows.
"""

import json
import sys
from datetime import date
from pathlib import Path


def ebird_week(day: date) -> int:
    return (day.month - 1) * 4 + min((day.day - 1) // 7, 3)


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("Usage: check_rare_bird.py SPECIES_CODE FREQUENCIES.json [YYYY-MM-DD]", file=sys.stderr)
        return 2
    try:
        day = date.fromisoformat(sys.argv[3]) if len(sys.argv) == 4 else date.today()
        frequencies = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        values = frequencies.get(sys.argv[1].lower(), [])
        frequency = float(values[ebird_week(day)]) if len(values) == 48 else 1.0
    except (OSError, ValueError, json.JSONDecodeError, IndexError):
        frequency = 1.0
    print(f"{frequency:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
