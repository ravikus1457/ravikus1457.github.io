# ravikus1457.github.io

Personal portfolio for **Ravi Kumar — Cloud & Network Engineer**.
Plain HTML/CSS/JS, hosted on GitHub Pages. Five pages, one shared stylesheet and script:

| page | what it holds |
|---|---|
| `index.html` | hero + topology, whoami, where to look, dated changelog |
| `production.html` | fleet status board, practices, edge architecture, shipped products |
| `labs.html` | lab 06 pipeline run, AWS labs (from `labs.json`), networking labs, building next, market scan |
| `experience.html` | timeline, skills, certs and education, résumé |
| `contact.html` | channels, what to ask about, logistics |

`scripts/check_site.py` (also run in CI by `site-check.yml`) asserts the header and footer are
byte-identical across pages, that every internal link, asset and `#anchor` resolves, and that each
page's canonical/og URL and the sitemap match. It is fault-tested: a drifted nav, a dead anchor and a
misspelled link each turn it red.

## Auto-updating labs
The **labs page** renders from `labs.json`, generated from the
[`aws-labs`](https://github.com/ravikus1457/aws-labs) repo:

- **In the cloud:** `.github/workflows/sync-labs.yml` re-generates `labs.json` daily
  (and on push / manual dispatch) — no machine needed.
- **From the Pi:** after a real lab run, `scripts/sync_from_pi.sh` regenerates from the
  local repo (including captured evidence) and pushes.

Regenerate manually: `python3 scripts/generate_labs.py ~/aws-devops-labs`
