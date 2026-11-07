#!/usr/bin/env python3
"""Build a sanitized example History preview from the generator template.

Not a release. Does not read the live workout store. Send and sync are pointed
at ./blocked-outbound. The FormSubmit alias is cleared.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "history_example.json")

EXTRA = {"target_overrides": {}, "features": {"cancel_relay": False}, "classes": [], "recovery": {}, "workout_whoop": {}}

OPEN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Synthetic local preview — Training History</title>
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
  <strong>EXAMPLE preview. Not current data and not a release.</strong> These sets are not the current log. Send and sync stay on this origin and fail.
</header>
<section>
  <p class="note">Serve this folder with a local web server. The chart is example pounds and kilograms, not a live log. The iframe is the same page embedded the way JARVIS embeds the dashboard.</p>
  <div class="row">
    <a class="btn" href="synthetic-history.html?tab=history&amp;ex=example-bench-press">History · example bench</a>
    <a class="btn" href="synthetic-history.html?tab=history&amp;ex=example-empty-press">History · no eligible load</a>
    <a class="btn" href="synthetic-history.html?tab=week">Week</a>
  </div>
  <div class="row">
    <button type="button" id="clear">Clear preview storage</button>
  </div>
  <p class="note" id="status">Opening History does not write a log. Clearing storage only removes preview keys in this browser.</p>
  <h2>JARVIS-style iframe</h2>
  <iframe title="Example training history" src="synthetic-history.html?tab=history&amp;ex=example-bench-press"></iframe>
</section>
<script src="storage-init.js"></script>
<script>
  var status = document.getElementById("status");
  document.getElementById("clear").onclick = function () { previewStorage.clear(); status.textContent = "Preview storage cleared."; };
</script>
</body>
</html>
"""

STORAGE_JS = """/* Example preview storage only. Not a live log. */
(function () {
  window.previewStorage = {
    clear: function () {
      ["tpDash.logs.v2", "tpDash.moves.v1", "tpDash.free.v1", "tpDash.sync.v1", "tpDash.syncapi.v1", "tpDash.syncq.v1"].forEach(function (k) {
        localStorage.removeItem(k);
      });
    }
  };
})();
"""


def render_page(template, store, extra=None):
    extra = EXTRA if extra is None else extra
    data = json.dumps(store, ensure_ascii=False).replace("</", "<\\/")
    extra_s = json.dumps(extra, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace("/*__DATA__*/null", data).replace("/*__EXTRA__*/null", extra_s).replace("__BUILT__", "example fixture · historical preview, not for publication")
    if not (extra or EXTRA).get("features", {}).get("cancel_relay"):
        html = re.sub(r"/\*RELAY\*/.*?/\*/RELAY\*/", "", html, flags=re.S)
    html = re.sub(r'const FS_TOKEN="[^"]*"', 'const FS_TOKEN=""', html)
    html = html.replace("https://formsubmit.co/ajax/", "./blocked-outbound/")
    html = html.replace("https://api.github.com", "./blocked-outbound")
    html = html.replace("<title>Training · Noah</title>", "<title>Training · synthetic local preview</title>")
    banner = "<!-- synthetic example preview; not a release; send and sync blocked -->\n"
    if not html.startswith(banner):
        html = banner + html
    return html


def assert_sanitized(html):
    banned = ["formsubmit.co", "api.github.com", "REDACTED_FORMSUBMIT_ALIAS"]
    for b in banned:
        if b in html:
            raise SystemExit("sanitization failed: found " + b)
    # The sync box keeps the visible hint "github_pat_…" from the generator. That is not a token.
    if re.search(r"github_pat_[A-Za-z0-9_]{8,}|ghp_[A-Za-z0-9]{8,}|gho_[A-Za-z0-9]{8,}", html):
        raise SystemExit("sanitization failed: token-shaped string")
    if 'const FS_TOKEN=""' not in html:
        raise SystemExit("token was not cleared")
    if "<canvas" in html.lower():
        raise SystemExit("preview used a canvas element")


def write_preview(out_dir, template_path=None, fixture_path=None):
    os.makedirs(out_dir, exist_ok=True)
    template = open(template_path or os.path.join(HERE, "template.html"), encoding="utf-8").read()
    store = json.load(open(fixture_path or FIXTURE, encoding="utf-8"))
    html = render_page(template, store)
    assert_sanitized(html)
    open(os.path.join(out_dir, "synthetic-history.html"), "w", encoding="utf-8").write(html)
    open(os.path.join(out_dir, "open.html"), "w", encoding="utf-8").write(OPEN_HTML)
    open(os.path.join(out_dir, "storage-init.js"), "w", encoding="utf-8").write(STORAGE_JS)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    write_preview(args.out)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
