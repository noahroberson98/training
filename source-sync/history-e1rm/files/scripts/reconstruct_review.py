#!/usr/bin/env python3
"""Rebuild a safe review page from the generator template and an exact safe page.

STORE and EXTRA are copied byte for byte. The build clock is copied from the
source page, so this does not claim a new TrainingPeaks read. The send token
is cleared and the send and sync hosts are replaced. This is not a release.
"""
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preview_current as current

CLOCK_RE = re.compile(r"built ([A-Z][a-z]{2} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M CT)")
BANNER = "<!-- CURRENT DATA NONPUBLISHABLE PREVIEW. Real recorded fitness data; not a release. Outbound send and sync are disabled. -->\n"


def reconstruct(template, source_html):
    store = current.extract_raw(source_html, "STORE")
    extra = current.extract_raw(source_html, "EXTRA")
    clocks = CLOCK_RE.findall(source_html)
    if len(clocks) != 1:
        raise SystemExit("source page must contain one build clock")
    if "/*__DATA__*/null" not in template or "/*__EXTRA__*/null" not in template:
        raise SystemExit("template is missing data placeholders")
    html = template.replace("/*__DATA__*/null", store, 1).replace("/*__EXTRA__*/null", extra, 1)
    html = current.strip_dormant_relay(html, extra)
    html = html.replace("__BUILT__", clocks[0])
    html = re.sub(
        r'const FS_TOKEN="[^"]*"; // FormSubmit alias for \+workout \(not a credential; same as JARVIS\)',
        'const FS_TOKEN=""; // review copy: live send destination removed',
        html,
        count=1,
    )
    html = html.replace('fetch("https://formsubmit.co/ajax/"+FS_TOKEN,', 'fetch("./blocked-outbound",')
    html = html.replace("https://api.github.com", "./blocked-outbound")
    html = html.replace(
        "<title>Training · Noah</title>",
        "<title>Training · current data nonpublishable preview</title>",
    )
    if not html.startswith("<!DOCTYPE html>\n"):
        raise SystemExit("template doctype changed")
    html = "<!DOCTYPE html>\n" + BANNER + html[len("<!DOCTYPE html>\n"):]
    if store not in html or extra not in html:
        raise SystemExit("STORE or EXTRA was not kept byte for byte")
    if "formsubmit.co" in html or "api.github.com" in html or "REDACTED_FORMSUBMIT_ALIAS" in html:
        raise SystemExit("review page still has a send host or placeholder token")
    if 'const FS_TOKEN=""' not in html or 'const FS_TOKEN="' in html.replace('const FS_TOKEN=""', "", 1):
        raise SystemExit("token was not cleared")
    if "/*RELAY*/" in html:
        raise SystemExit("dormant relay remains")
    return html, store, extra, clocks[0]


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: reconstruct_review.py template.html exact-safe.html out.html")
    template = Path(sys.argv[1]).read_text(encoding="utf-8")
    source = Path(sys.argv[2]).read_text(encoding="utf-8")
    html, store, extra, clock = reconstruct(template, source)
    out = Path(sys.argv[3])
    out.write_text(html, encoding="utf-8")
    print("clock " + clock)
    print("bytes " + str(out.stat().st_size))
    print("sha256 " + hashlib.sha256(out.read_bytes()).hexdigest())
    print("STORE " + hashlib.sha256(store.encode()).hexdigest())
    print("EXTRA " + hashlib.sha256(extra.encode()).hexdigest())


if __name__ == "__main__":
    main()
