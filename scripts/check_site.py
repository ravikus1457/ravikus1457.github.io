#!/usr/bin/env python3
"""Structural check for the multi-page portfolio. Exit 1 on any finding.

- every top-level page shares byte-identical <header class="nav"> and <footer> blocks
  (except the aria-current marker, which must point at the page itself)
- every relative href/src resolves to a file in the repo
- every in-page or cross-page #anchor resolves to an element id on the target page
- each page has a <title>, a canonical URL that matches its filename, and og:url == canonical
Run: python3 scripts/check_site.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://ravikus1457.github.io/"
PAGES = ["index.html", "production.html", "labs.html", "experience.html", "contact.html"]
findings = []


def block(html, tag, cls):
    m = re.search(rf'<{tag} class="{cls}".*?</{tag}>', html, re.S)
    return m.group(0) if m else None


def ids_in(html):
    return set(re.findall(r'\bid="([^"]+)"', html))


docs = {p: (ROOT / p).read_text(encoding="utf-8") for p in PAGES}
ids = {p: ids_in(h) for p, h in docs.items()}

# shared header / footer
ref_nav = None
ref_foot = None
for p, h in docs.items():
    nav = block(h, "header", "nav")
    foot = block(h, "footer", "foot")
    if not nav or not foot:
        findings.append(f"{p}: missing header.nav or footer.foot"); continue
    stem = p.replace(".html", "")
    cur = re.findall(r'<a href="([^"]+)" aria-current="page">', nav)
    if cur != [f"{stem}.html"]:
        findings.append(f"{p}: aria-current points at {cur}, expected ['{stem}.html']")
    nav_norm = nav.replace(' aria-current="page"', "")
    if ref_nav is None:
        ref_nav, ref_foot = nav_norm, foot
    else:
        if nav_norm != ref_nav: findings.append(f"{p}: header differs from index.html")
        if foot != ref_foot: findings.append(f"{p}: footer differs from index.html")

# links, assets, anchors, metadata
for p, h in docs.items():
    for attr, target in re.findall(r'\b(href|src|poster)="([^"]+)"', h):
        if target.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#")):
            if target.startswith("#") and target != "#":
                if target[1:] not in ids[p]: findings.append(f"{p}: anchor {target} has no id on this page")
            continue
        path, _, frag = target.partition("#")
        if not (ROOT / path).exists():
            findings.append(f"{p}: {attr} -> {target} does not exist"); continue
        if frag and path in ids and frag not in ids[path]:
            findings.append(f"{p}: anchor {target} has no id on {path}")
    if not re.search(r"<title>[^<]+</title>", h): findings.append(f"{p}: no <title>")
    want = SITE if p == "index.html" else SITE + p
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    og = re.search(r'<meta property="og:url" content="([^"]+)"', h)
    if not canon or canon.group(1) != want: findings.append(f"{p}: canonical {canon and canon.group(1)} != {want}")
    if not og or og.group(1) != want: findings.append(f"{p}: og:url {og and og.group(1)} != {want}")
    if 'data-page="' + p.replace(".html", "") + '"' not in h: findings.append(f"{p}: body data-page mismatch")

# sitemap lists exactly the pages
sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8") if (ROOT / "sitemap.xml").exists() else ""
for p in PAGES:
    want = SITE if p == "index.html" else SITE + p
    if f"<loc>{want}</loc>" not in sm: findings.append(f"sitemap.xml: missing {want}")

for f in findings: print("FAIL:", f)
print(f"{'FAIL' if findings else 'OK'}: {len(PAGES)} pages, {len(findings)} findings")
sys.exit(1 if findings else 0)
