#!/usr/bin/env python3
"""Generate labs.json for the portfolio from the aws-labs repo.

Single source of truth = the "What's inside" table in the aws-labs README, plus
each lab folder's README and any captured evidence. Re-run this whenever the labs
change (or let the GitHub Action / runner hook do it) so the portfolio's Labs
section stays in sync automatically.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

LABS_REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "aws-devops-labs"
GH_USER = "ravikus1457"
GH_REPO = "aws-labs"
OUT = Path(__file__).resolve().parent.parent / "labs.json"

ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")


def parse_readme_table(readme: Path):
    labs = []
    if not readme.exists():
        return labs
    for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
        m = ROW.match(line.strip())
        if not m:
            continue
        num, title, path, demonstrates, cost = m.groups()
        slug = path.strip().rstrip("/").split("/")[-1]
        labs.append({
            "id": num.zfill(2),
            "title": title.strip(),
            "slug": slug,
            "demonstrates": demonstrates.strip(),
            "cost": cost.strip(),
            "tags": [t.strip() for t in re.split(r",| and ", demonstrates) if t.strip()][:6],
            "repo_url": f"https://github.com/{GH_USER}/{GH_REPO}/tree/main/{path.strip()}",
            "has_evidence": (LABS_REPO / path.strip() / "evidence").exists()
            or any((LABS_REPO / "evidence").glob(f"{num.zfill(2)}*")),
        })
    return labs


def main():
    labs = parse_readme_table(LABS_REPO / "README.md")
    payload = {
        "generated_from": str(LABS_REPO),
        "repo": f"https://github.com/{GH_USER}/{GH_REPO}",
        "count": len(labs),
        "labs": labs,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} with {len(labs)} labs")


if __name__ == "__main__":
    main()
