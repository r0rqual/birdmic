#!/usr/bin/env python3
"""Convert an eBird bar-chart TSV export into weekly species frequencies.

Usage:
    python3 scripts/parse_ebird_barchart.py BARCHART.tsv TAXONOMY.csv OUTPUT.json

Download a bar-chart export for your chosen eBird region and the current eBird
taxonomy CSV, then pass their paths to this script. The output maps eBird
species codes to 48 frequencies, one for each eBird week of the year.
"""

import csv
import json
import sys
from pathlib import Path


def load_taxonomy(taxonomy_file: Path) -> dict[str, str]:
    """Return common-name to eBird-species-code mappings from a taxonomy CSV."""
    names: dict[str, str] = {}
    with taxonomy_file.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            common_name = row.get("PRIMARY_COM_NAME", "").strip()
            species_code = row.get("SPECIES_CODE", "").strip().lower()
            if not common_name or not species_code:
                continue
            names[common_name] = species_code
            names.setdefault(common_name.split(" (", 1)[0], species_code)
    return names


def parse_barchart(barchart_file: Path, names: dict[str, str]) -> tuple[dict[str, list[float]], list[str]]:
    """Parse a bar-chart TSV export, returning frequencies and unmatched names."""
    frequencies: dict[str, list[float]] = {}
    unmatched: list[str] = []
    with barchart_file.open(encoding="utf-8") as source:
        for raw_line in source:
            columns = raw_line.rstrip("\n").split("\t")
            if len(columns) < 49:
                continue
            species_name = columns[0].strip()
            normalized_name = species_name.lower()
            if (
                not species_name
                or normalized_name == "species"
                or normalized_name.startswith("sample size")
                or "january" in normalized_name
            ):
                continue
            try:
                weeks = [float(value.strip() or 0) for value in columns[1:49]]
            except ValueError:
                continue
            species_code = names.get(species_name)
            if species_code:
                frequencies[species_code] = weeks
            else:
                unmatched.append(species_name)
    return frequencies, unmatched


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: parse_ebird_barchart.py BARCHART.tsv TAXONOMY.csv OUTPUT.json", file=sys.stderr)
        return 2

    barchart_file, taxonomy_file, output_file = map(Path, sys.argv[1:])
    names = load_taxonomy(taxonomy_file)
    frequencies, unmatched = parse_barchart(barchart_file, names)
    if not frequencies:
        print("No species frequencies were parsed; refusing to write output", file=sys.stderr)
        return 1
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(frequencies, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(frequencies)} species to {output_file}")
    if unmatched:
        print(f"Warning: {len(unmatched)} species were absent from the taxonomy; first few:")
        for species_name in unmatched[:10]:
            print(f"  - {species_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
