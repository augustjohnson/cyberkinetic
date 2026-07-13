#!/usr/bin/env python3
"""STUB for skill: render-assessment. See skills/render-assessment/SKILL.md."""
import argparse
from _stub import announce


def main():
    p = argparse.ArgumentParser(description="Render unranked findings for curation (STUB)")
    p.add_argument("--db", required=True)
    p.add_argument("--assessment", required=True)
    p.add_argument("--out", required=True,
                   help="access-controlled output dir (NEVER a public location)")
    args = p.parse_args()

    announce(
        "render-assessment",
        "render claims + verdicts as an unranked, access-controlled view",
        args,
        [
            "SELECT claims + citations + verdicts for this assessment",
            "render UNRANKED; each finding shows citation (resolvable to SHA/line) "
            "+ verdict (incl. uncertain) + consequence context",
            "source_severity shown as the tool's opinion, NOT as a ranking",
            "grouping by rule allowed for readability (presentation only)",
            "WRITE to an access-controlled path (HARD-GATE: never public internet)",
            "INSERT render_output(path, rendered_at)",
            "UPDATE assessment SET status='rendered'",
        ],
    )


if __name__ == "__main__":
    main()
