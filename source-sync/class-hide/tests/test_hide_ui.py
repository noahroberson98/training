"""Retired standalone demo. The review proof is test_template_mobile.py on assembled/current.html."""
import hashlib, os, sys, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ok = True

def check(c, m):
    global ok
    print(("PASS " if c else "FAIL ") + m)
    ok = ok and bool(c)

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(HERE)))
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
from playwright.sync_api import sync_playwright
shots = HERE / "shots"
shots.mkdir(exist_ok=True)
INIT = r"""
(() => {
  const orig = Storage.prototype.setItem;
  Storage.prototype.setItem = function (k, v) {
    if (window.__failStorage && k === "tpDash.classOverrides.v1") throw new DOMException("quota", "QuotaExceededError");
    return orig.call(this, k, v);
  };
})();
"""
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    ctx.add_init_script(INIT)
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
    page = ctx.new_page()
    page.goto(f"http://127.0.0.1:{port}/class-hide.html", wait_until="networkidle")
    check(page.locator("[data-key='2099-01-03|09:00|THIS STRENGTH']").count() == 1, "unrelated booking is listed")
    page.screenshot(path=str(shots / "mobile-before.png"))
    page.locator("[data-key='2099-01-01|10:00|APEX'] button").click()
    hidden = page.locator("#hidden [data-key='2099-01-01|10:00|APEX']")
    check(hidden.count() == 1 and hidden.locator("button").inner_text() == "Undo", "hide moves that row and shows Undo")
    check("gym list still says reserved" in hidden.inner_text().lower(), "hidden row keeps the gym reserved label")
    check(page.locator("#booked [data-key='2099-01-03|09:00|THIS STRENGTH']").count() == 1, "the other booking stays booked")
    page.screenshot(path=str(shots / "mobile-hidden.png"))
    page.reload(wait_until="networkidle")
    check(page.locator("#hidden [data-key='2099-01-01|10:00|APEX']").count() == 1, "hide survives reload")
    page.click("#reimport")
    check(page.locator("#hidden [data-key='2099-01-01|10:00|APEX']").count() == 1, "stale reserved feed does not restore the hidden row")
    check(page.locator("#booked [data-key='2099-01-02|10:00|APEX']").count() == 1, "the row missing from the feed is still available to hide")
    page.locator("#booked [data-key='2099-01-02|10:00|APEX'] button").click()
    page.click("#reimport")
    check(page.locator("#hidden [data-key='2099-01-02|10:00|APEX']").count() == 1, "a missing feed row stays hidden after reload of the feed")
    page.locator("#hidden [data-key='2099-01-01|10:00|APEX'] button").click()
    check(page.locator("#booked [data-key='2099-01-01|10:00|APEX']").count() == 1, "undo puts the row back")
    check("you reported this cancelled" in page.locator("[data-key='2099-01-01|10:00|APEX']").inner_text().lower(), "undo does not pretend the gym cancelled it")
    page.screenshot(path=str(shots / "mobile-undo.png"))
    page.evaluate("() => { window.__failStorage = true; }")
    page.locator("#booked [data-key='2099-01-03|09:00|THIS STRENGTH'] button").click()
    check(page.locator("#saveWarn").is_visible() and page.locator("#booked [data-key='2099-01-03|09:00|THIS STRENGTH']").count() == 1, "a failed save does not claim the row was hidden")
    page.screenshot(path=str(shots / "mobile-save-failed.png"))
    browser.close()
httpd.shutdown()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
