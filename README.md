# ravikus1457.github.io

Personal portfolio for **Ravi Kumar — Cloud & Network Engineer**.
Plain HTML/CSS/JS, hosted on GitHub Pages.

## Auto-updating labs
The **Labs** section renders from `labs.json`, generated from the
[`aws-labs`](https://github.com/ravikus1457/aws-labs) repo:

- **In the cloud:** `.github/workflows/sync-labs.yml` re-generates `labs.json` daily
  (and on push / manual dispatch) — no machine needed.
- **From the Pi:** after a real lab run, `scripts/sync_from_pi.sh` regenerates from the
  local repo (including captured evidence) and pushes.

Regenerate manually: `python3 scripts/generate_labs.py ~/aws-devops-labs`
