#!/bin/bash
# Two-pass build: render once, read heading pages from the PDF, rebuild with real TOC numbers.
set -e
cd "$(dirname "$0")"
SK=/root/.claude/skills/synced/6d0fc220-0e05-4ecc-a33f-936277bd5906_29155d69-168d-4c53-a197-a0a042912cb8/docx
rm -f toc_pages.json
for pass in 1 2; do
  node build_proposal.js
  python3 $SK/scripts/office/soffice.py --headless --convert-to pdf GTR70E_WYVERN_Research_Proposal.docx >/dev/null 2>&1
  python3 - <<'PY'
import json, subprocess, re
entries = json.load(open("toc_entries.json"))
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo","GTR70E_WYVERN_Research_Proposal.pdf"],capture_output=True,text=True).stdout).group(1))
pages = [subprocess.run(["pdftotext","-f",str(i),"-l",str(i),"-layout","GTR70E_WYVERN_Research_Proposal.pdf","-"],capture_output=True,text=True).stdout for i in range(1,n+1)]
norm = lambda t: re.sub(r"\s+"," ",t)
out = {}; start = 2
for e in entries:
    if e == "Table of Contents": out[e] = 1; continue
    key = norm(e)[:45]
    for i in range(start, n):
        lines = [norm(l).strip() for l in pages[i].splitlines()]
        if any(l == norm(e) or (len(e) > 45 and l.startswith(key)) for l in lines):
            out[e] = i; start = i; break
json.dump(out, open("toc_pages.json","w"), indent=1)
print(len(out), "of", len(entries), "found;", n, "pages")
PY
done
