#!/usr/bin/env python3
"""Build a nonpublishable History preview from a sanitized current page.

STORE and EXTRA are copied byte for byte from the source page. The FormSubmit
alias is cleared and the default send and sync hosts are blocked. This is not
a production send configuration.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def extract_raw(html, name):
    key = "const %s = " % name
    i = html.find(key)
    if i < 0:
        raise SystemExit("missing " + name)
    raw = html[i + len(key):]
    _, end = json.JSONDecoder().raw_decode(raw)
    return raw[:end]


def built_label(source_html):
    """Use the source page's own CT clock when it is actually printed there."""
    m = re.search(r"built ([A-Z][a-z]{2} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M CT)", source_html)
    if m:
        return m.group(1) + " · historical preview, not for publication"
    return "historical preview, not for publication"


def strip_dormant_relay(html, extra_raw):
    """Match build.py: the issue-link branch is removed when the feature is off."""
    extra = json.loads(extra_raw)
    if not (extra.get("features") or {}).get("cancel_relay"):
        html = re.sub(r"/\*RELAY\*/.*?/\*/RELAY\*/", "", html, flags=re.S)
    return html


def render_page(template, source_html):
    store = extract_raw(source_html, "STORE")
    extra = extract_raw(source_html, "EXTRA")
    if template.find("/*__DATA__*/null") < 0 or template.find("/*__EXTRA__*/null") < 0:
        raise SystemExit("template is missing data placeholders")
    html = template.replace("/*__DATA__*/null", store, 1).replace("/*__EXTRA__*/null", extra, 1)
    if store not in html or extra not in html:
        raise SystemExit("STORE or EXTRA was not kept byte for byte")
    html = strip_dormant_relay(html, extra)
    html = html.replace("__BUILT__", built_label(source_html))
    html = re.sub(r'const FS_TOKEN="[^"]*"', 'const FS_TOKEN=""', html, count=1)
    html = html.replace("https://formsubmit.co/ajax/", "./blocked-outbound/")
    html = html.replace("https://api.github.com", "./blocked-outbound")
    html = html.replace("<title>Training · Noah</title>", "<title>Training · historical preview, not for publication</title>")
    banner = "<!-- historical preview, not for publication; recorded data; send and sync blocked -->\n"
    if not html.startswith(banner):
        html = banner + html
    if "formsubmit.co" in html or "api.github.com" in html or "REDACTED_FORMSUBMIT_ALIAS" in html:
        raise SystemExit("preview still has a send host or placeholder token")
    if 'const FS_TOKEN=""' not in html:
        raise SystemExit("token was not cleared")
    return html, store, extra


OPEN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Historical preview, not for publication — Training History</title>
<style>
  body{margin:0;font:15px/1.45 -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;background:#111;color:#eee}
  header,section{padding:16px 20px}
  header{background:#222}
  a{color:#9ab}
  .row{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
  button,a.btn{background:#2a2a32;color:#eee;border:1px solid #444;border-radius:8px;padding:8px 12px;text-decoration:none}
  iframe{width:100%;height:900px;border:0;background:#000}
  .note{color:#bbb;max-width:70ch}
</style>
</head>
<body>
<header>
  <strong>Historical preview, not for publication.</strong> Recorded data from the sanitized snapshot. Not a release and not a live JARVIS review. Send and sync stay on this origin and fail.
</header>
<section>
  <p class="note">This iframe embeds the History page the way a host page can embed the dashboard. It is a local preview, not a live JARVIS review. STORE and EXTRA are the sanitized current snapshot.</p>
  <div class="row">
    <a class="btn" href="current-history.html?tab=history&amp;ex=machine-row">History · Machine Row</a>
    <a class="btn" href="current-history.html?tab=history&amp;ex=abmat-sit-up">History · no eligible load</a>
    <a class="btn" href="current-history.html?tab=week&amp;day=2026-11-06">Week</a>
  </div>
  <h2>Embed</h2>
  <iframe title="Current training history" src="current-history.html?tab=history&amp;ex=machine-row"></iframe>
</section>
</body>
</html>
"""


def write_preview(out_dir, template_path, source_html_path):
    os.makedirs(out_dir, exist_ok=True)
    template = open(template_path, encoding="utf-8").read()
    source = open(source_html_path, encoding="utf-8").read()
    html, store, extra = render_page(template, source)
    open(os.path.join(out_dir, "current-history.html"), "w", encoding="utf-8").write(html)
    open(os.path.join(out_dir, "open.html"), "w", encoding="utf-8").write(OPEN_HTML)
    # Prove the embedded JSON matches the source page exactly.
    built = open(os.path.join(out_dir, "current-history.html"), encoding="utf-8").read()
    if extract_raw(built, "STORE") != store or extract_raw(built, "EXTRA") != extra:
        raise SystemExit("built preview STORE/EXTRA drifted")
    if extract_raw(source, "STORE") != store or extract_raw(source, "EXTRA") != extra:
        raise SystemExit("source STORE/EXTRA drifted")
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=os.path.join(HERE, "template.html"))
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    write_preview(args.out, args.template, args.source)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
