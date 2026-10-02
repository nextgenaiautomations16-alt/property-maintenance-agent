"""
Generates synthetic tenant maintenance messages plus a labeled ground
truth of the expected urgency classification -- including the exact
water-through-the-ceiling scenario from the job posting this project was
built to demonstrate competence for.

Run: python generate_synthetic_cases.py
Outputs: synthetic_cases.json, ground_truth.csv
"""
import json
import csv
from pathlib import Path

CASES = [
    # (tenant_name, property_id, unit_id, message, expected_urgency, note)
    ("M. Chen", "PROP-101", "3B", "There is water coming through the ceiling. I tried calling and nobody answered.", "high", "the exact scenario from the job posting"),
    ("J. Alvarez", "PROP-204", "12", "I smell gas in the kitchen, it's pretty strong.", "critical", "life-safety, must never be missed"),
    ("R. Patel", "PROP-101", "5A", "My smoke detector is going off and I can smell smoke near the stove.", "critical", "fire risk"),
    ("K. Novak", "PROP-204", "7", "The kitchen faucet has been dripping for a few days, not urgent.", "routine", "clearly routine"),
    ("T. Osei", "PROP-101", "2C", "Bathroom light bulb burned out, could someone replace it when convenient.", "routine", "clearly routine"),
    ("S. Kowalski", "PROP-204", "9", "No heat in the apartment since this morning, it's freezing.", "high", "loss of essential utility"),
    ("L. Rossi", "PROP-101", "1A", "The front door hinge is squeaking loudly.", "routine", "clearly routine"),
    ("D. Nakamura", "PROP-204", "4B", "There's sewage backing up into the bathtub.", "high", "property damage + health risk"),
    ("A. Fischer", "PROP-101", "6C", "Power went out in half the unit, breaker won't reset.", "high", "loss of essential utility"),
    ("P. Delgado", "PROP-204", "11", "Carbon monoxide detector is beeping.", "critical", "life-safety"),
    ("J. Alvarez", "PROP-101", "3B", "The toilet keeps running after flushing, wastes water.", "routine", "clearly routine"),
    ("M. Chen", "PROP-204", "6", "Screen door off its track, minor repair whenever.", "routine", "clearly routine"),
    ("R. Patel", "PROP-101", "8B", "There's a strange burning smell coming from the electrical panel.", "critical", "fire/electrical risk"),
    ("K. Novak", "PROP-204", "3", "My apartment flooded overnight, water is an inch deep in the hallway.", "high", "active property-damage risk"),
    ("T. Osei", "PROP-101", "4A", "Kind of a weird message, not sure how to describe it, something feels off with the unit but I can't tell what.", "high", "ambiguous -- should route to LLM and default cautiously"),
]


def main():
    out_dir = Path(__file__).parent
    cases = []
    ground_truth_rows = []

    for i, (name, prop, unit, message, expected, note) in enumerate(CASES):
        case_id = f"CASE{i+1:03d}"
        cases.append({
            "case_id": case_id, "tenant_name": name, "property_id": prop,
            "unit_id": unit, "message": message,
        })
        ground_truth_rows.append({"case_id": case_id, "expected_urgency": expected, "note": note})

    with open(out_dir / "synthetic_cases.json", "w") as f:
        json.dump(cases, f, indent=2)
    with open(out_dir / "ground_truth.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "expected_urgency", "note"])
        writer.writeheader()
        writer.writerows(ground_truth_rows)

    print(f"Generated {len(cases)} synthetic tenant messages.")


if __name__ == "__main__":
    main()
