#!/usr/bin/env python3
"""Print an eBird species frequency for a date from BirdMic frequency JSON.

Usage:
    python3 scripts/check_rare_bird.py SPECIES_CODE FREQUENCIES.json [YYYY-MM-DD]

An unknown species is reported as 1.0 (common/unknown), which is a safe default
for alert workflows. Invalid dates and unreadable or malformed datasets exit
nonzero so operational failures remain distinguishable from lookup results.
"""

import json
import sys
from datetime import date
from pathlib import Path


def ebird_week(day: date) -> int:
    return (day.month - 1) * 4 + min((day.day - 1) // 7, 3)


def lookup_frequency(
    frequencies: object, species_code: str, day: date
) -> float:
    """Return this period's frequency, defaulting unknown species to common."""
    if not isinstance(frequencies, dict):
        raise ValueError("frequency data must be a JSON object")

    values = frequencies.get(species_code.strip().lower())
    if values is None:
        return 1.0
    if not isinstance(values, list) or len(values) != 48:
        raise ValueError("species frequency must contain exactly 48 periods")

    value = values[ebird_week(day)]
    if isinstance(value, bool):
        raise ValueError("species frequency must be numeric")
    frequency = float(value)
    if not 0.0 <= frequency <= 1.0:
        raise ValueError("species frequency must be between 0.0 and 1.0")
    return frequency


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("Usage: check_rare_bird.py SPECIES_CODE FREQUENCIES.json [YYYY-MM-DD]", file=sys.stderr)
        return 2
    try:
        day = date.fromisoformat(sys.argv[3]) if len(sys.argv) == 4 else date.today()
        frequencies = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        frequency = lookup_frequency(frequencies, sys.argv[1], day)
    except (OSError, ValueError, json.JSONDecodeError, IndexError) as error:
        print(f"check_rare_bird.py: {error}", file=sys.stderr)
        return 1
    print(f"{frequency:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
