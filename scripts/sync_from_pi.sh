#!/usr/bin/env bash
# Regenerate labs.json from the local aws-devops-labs repo and push the portfolio.
# Hook this into the lab runner (call it after a lab run) for hands-off updates.
set -e
cd "$(dirname "$0")/.."
python3 scripts/generate_labs.py "$HOME/aws-devops-labs"
if [ -n "$(git status --porcelain labs.json)" ]; then
  git add labs.json && git commit -m "chore: sync labs.json (local run)" && git push
else
  echo "labs.json unchanged"
fi
