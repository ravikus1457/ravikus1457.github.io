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

ROW = re.compile(r"^\|\s*([A-Za-z]?\d+)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
HEADING = re.compile(r"^#{1,3}\s+(.*)")


def parse_readme_table(readme: Path):
    labs = []
    if not readme.exists():
        return labs
    section = ""
    for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
        h = HEADING.match(line.strip())
        if h:
            section = h.group(1).lower()
            continue
        m = ROW.match(line.strip())
        if not m:
            continue
        num, title, path, demonstrates, meta = m.groups()
        path = path.strip()
        category = "networking" if "network" in section else "cloud"
        lab_id = num if any(c.isalpha() for c in num) else num.zfill(2)
        labs.append({
            "id": lab_id,
            "category": category,
            "title": title.strip(),
            "slug": path.rstrip("/").split("/")[-1],
            "demonstrates": demonstrates.strip(),
            "meta": meta.strip(),                 # cost (cloud) or stack (networking)
            "tags": [t.strip() for t in re.split(r",| and ", demonstrates) if t.strip()][:6],
            "repo_url": f"https://github.com/{GH_USER}/{GH_REPO}/tree/main/{path}",
            "has_evidence": (LABS_REPO / path / "evidence").exists(),
        })
    return labs


def main():
    labs = parse_readme_table(LABS_REPO / "README.md")
    cloud = [l for l in labs if l["category"] == "cloud"]
    net = [l for l in labs if l["category"] == "networking"]
    payload = {
        "generated_from": str(LABS_REPO),
        "repo": f"https://github.com/{GH_USER}/{GH_REPO}",
        "count": len(labs),
        "labs": cloud,
        "networking": net,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}: {len(cloud)} cloud + {len(net)} networking labs")


if __name__ == "__main__":
    main()
