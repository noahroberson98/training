"""Browser hit-testing for the save-failure UI. Does not rewrite the page.

Usage: python3 tests/test_e1rm_reach.py exact.html [screenshot_dir]

Clicks are real pointer clicks. No force click, injected button, or handler dispatch.
"""
import hashlib
import shutil
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

KEY = "2026-11-06|Upper Body"
WINDOW = ["2026-11-06T15:00:38.635Z", "2026-11-06T15:12:12.324Z"]
FULL = "A reload drops them. A workout already emailed is not marked sent on this phone, so Done could send it again after a reload. Nothing resends by itself."
INIT = r"""
(() => {
  const orig = Storage.prototype.setItem;
  Storage.prototype.setItem = function (key, value) {
    if (key === "tpDash.logs.v2" && (sessionStorage.getItem("__storageMode") || "") === "quota") {
      throw new DOMException("quota", "QuotaExceededError");
    }
    return orig.call(this, key, value);
  };
})();
"""

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

ok = True
def check(c, m):
    global ok
    print(("PASS " if c else "FAIL ") + m)
    ok = ok and bool(c)

if len(sys.argv) < 2:
    print("FAIL exact HTML path required")
    sys.exit(2)
src = Path(sys.argv[1]).resolve()
shot_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
before = sha256(src)
print("BOUND sha256 " + before + " bytes " + str(src.stat().st_size))
if shot_dir:
    shot_dir.mkdir(parents=True, exist_ok=True)
serve = Path("/tmp/reach-serve")
if serve.exists():
    shutil.rmtree(serve)
serve.mkdir()
shutil.copy2(src, serve / "exact.html")

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return
httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(serve)))
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % port

from playwright.sync_api import sync_playwright
CHROME = "/usr/bin/google-chrome"
state = {"hits": 0, "mode": "500"}
hashes = []

def route_all(route):
    url = route.request.url
    if "blocked-outbound" in url:
        state["hits"] += 1
        if state["mode"] == "500":
            route.fulfill(status=500, content_type="application/json", body='{"success":"false"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"success":"true"}')
        return
    host = url.split("/")[2] if url.startswith("http") else ""
    if host.startswith("127.0.0.1"):
        route.continue_()
    else:
        route.abort()

def snap(page, name, w, h, scale):
    if not shot_dir:
        return
    path = shot_dir / name
    page.screenshot(path=str(path))
    doc = page.evaluate("() => document.documentElement.outerHTML")
    box = page.evaluate("() => ({vw:window.innerWidth, vh:window.innerHeight, dpr:window.devicePixelRatio})")
    hashes.append({"name": name, "viewport": [w, h], "device_scale_factor": scale, "measured": box, "png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "png_bytes": path.stat().st_size, "document_sha256": hashlib.sha256(doc.encode()).hexdigest()})

HIT = """(sel) => {
  const el = document.querySelector(sel);
  if (!el || el.hidden) return {ok:false, missing:!el, hidden:!!(el && el.hidden)};
  el.scrollIntoView({block:'center', inline:'nearest'});
  const r = el.getBoundingClientRect();
  const x = r.left + r.width / 2;
  const y = r.top + r.height / 2;
  const top = document.elementFromPoint(x, y);
  const msg = el.querySelector('#saveFailMsg, #toastMsg') || el;
  return {
    ok: !!(top && (top === el || el.contains(top))),
    id: top ? top.id : '',
    left: r.left, right: r.right, topY: r.top, bottom: r.bottom,
    vw: innerWidth, vh: innerHeight,
    sw: msg.scrollWidth, cw: msg.clientWidth,
    inView: r.top >= -1 && r.left >= -1 && r.bottom <= innerHeight + 1 && r.right <= innerWidth + 1
  };
}"""

def hit(page, sel):
    return page.evaluate(HIT, sel)

def readable(info):
    return info.get("ok") and info.get("inView") and info.get("sw", 0) <= info.get("cw", 0) + 1 and info.get("left", -1) >= -1 and info.get("right", 9999) <= info.get("vw", 0) + 1

def prove_actions(page, tag):
    """Scroll Copy summary and Done into view after a successful retry. The frame taken before this scroll is not claimed to show them."""
    page.locator("#sheet .acts").evaluate("el => el.scrollIntoView({block:'center', inline:'nearest'})")
    posts = state["hits"]
    focused = []
    for sel, name in (("#sumCopy", "Copy summary"), ("#sumClose", "Done")):
        page.locator(sel).focus()
        info = hit(page, sel)
        active = page.evaluate("() => document.activeElement && document.activeElement.id")
        focused.append(active)
        check(readable(info) and active == sel[1:], tag + " after successful retry " + name + " is scrolled into view, focused, and is the pointer hit")
    print("ACTIONS %s post=%d focus=%s" % (tag, posts, ",".join(focused)))
    return posts

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    for width, height, scale, tag in ((1280, 900, 1, "desktop"), (390, 844, 2, "mobile")):
        ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale)
        ctx.add_init_script(INIT)
        ctx.route("**/*", route_all)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        state["hits"] = 0
        state["mode"] = "500"
        page.goto(base + "/exact.html?tab=workout&day=2026-11-06", wait_until="networkidle")
        page.evaluate("() => sessionStorage.setItem('__storageMode','quota')")
        page.reload(wait_until="networkidle")
        page.click("[data-complete='%s']" % KEY)
        page.wait_for_selector("#sumRetry")
        check(page.locator("#sheet").count() == 1, tag + " failed summary dialog is open")
        for sel, name in (("#sumRetry", "Retry Save"), ("#sumCopy", "Copy summary"), ("#sumClose", "Done")):
            info = hit(page, sel)
            check(readable(info), tag + " " + name + " is hit at its center and inside the viewport")
        page.locator("#sumRetry").focus()
        check(page.evaluate("() => document.activeElement && document.activeElement.id") == "sumRetry", tag + " Retry Save takes keyboard focus")
        hits = state["hits"]
        page.click("#sumRetry")
        page.wait_for_timeout(200)
        check(state["hits"] == hits and "Not saved on this phone." in page.locator("#sumSync").inner_text() and page.locator("#sheet").count() == 1, tag + " failed Retry Save inside the summary does not send")
        page.locator("#sumRetry").focus()
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        check(state["hits"] == hits and page.locator("#sumRetry").is_visible(), tag + " Enter on failed Retry Save does not send")
        snap(page, tag + "-summary-failed.png", width, height, scale)
        page.evaluate("() => sessionStorage.setItem('__storageMode','ok')")
        page.click("#sumRetry")
        page.wait_for_timeout(200)
        check(state["hits"] == hits and page.locator("#sumRetry").count() and not page.locator("#sumRetry").is_visible(), tag + " successful Retry Save inside the summary does not send")
        check("Saved on this phone only." in page.locator("#sumSync").inner_text(), tag + " summary label says saved after Retry Save")
        window = page.evaluate("""() => { const w=W.find(x=>x.key==='2026-11-06|Upper Body'); return [w.started_at, w.ended_at, (local[w.key]||{}).completed_at||null]; }""")
        check(window[0:2] == WINDOW and window[2], tag + " recorded window stays 11:33 and completed_at is set")
        print("RETRY %s post_before_scroll=%d" % (tag, state["hits"]))
        snap(page, tag + "-summary-retry.png", width, height, scale)
        prove_actions(page, tag + " summary")
        snap(page, tag + "-summary-retry-actions.png", width, height, scale)
        ctx.close()

        ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale)
        ctx.add_init_script(INIT)
        ctx.route("**/*", route_all)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        state["hits"] = 0
        state["mode"] = "200"
        page.goto(base + "/exact.html?tab=workout&day=2026-11-06", wait_until="networkidle")
        page.evaluate("() => sessionStorage.setItem('__storageMode','quota')")
        page.reload(wait_until="networkidle")
        page.click("[data-complete='%s']" % KEY)
        page.wait_for_selector("#sumClose")
        page.click("#sumClose")
        page.wait_for_timeout(400)
        check(state["hits"] == 1 and page.locator("#sheet").count() == 1, tag + " local 200 with a failed save leaves the summary open")
        warn = page.locator("#saveFailMsg").inner_text()
        toast = page.locator("#toastMsg").inner_text()
        check(FULL in warn and "Workout emailed. Not saved on this phone." in toast, tag + " warning keeps the resend meaning and the toast names the unsaved email")
        for sel, name in (("#saveFailMsg", "warning"), ("#toastMsg", "toast"), ("#sumRetry", "Retry Save"), ("#sumCopy", "Copy summary"), ("#sumClose", "Done")):
            info = hit(page, sel)
            check(readable(info), tag + " after 200 " + name + " is fully readable")
        opaque = page.evaluate("""() => {
          const c = getComputedStyle(document.getElementById('saveFail')).backgroundColor;
          const m = c.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
          return {c, alpha: m ? (m[4] == null ? 1 : Number(m[4])) : -1};
        }""")
        check(opaque["alpha"] == 1, tag + " warning background is opaque")
        hits = state["hits"]
        page.click("#sumRetry")
        page.wait_for_timeout(150)
        check(state["hits"] == hits, tag + " Retry Save after the email does not send again while storage still fails")
        page.locator("#sumSync").scroll_into_view_if_needed()
        snap(page, tag + "-after-200-failed.png", width, height, scale)
        page.evaluate("() => sessionStorage.setItem('__storageMode','ok')")
        page.click("#sumRetry")
        page.wait_for_timeout(200)
        check(state["hits"] == hits and "Saved on this phone." in page.locator("#toastMsg").inner_text(), tag + " Retry Save after the email persists without another send")
        print("RETRY %s after200 post_before_scroll=%d" % (tag, state["hits"]))
        snap(page, tag + "-after-200-retry.png", width, height, scale)
        prove_actions(page, tag + " after200")
        snap(page, tag + "-after-200-actions.png", width, height, scale)
        page.click("#sumCopy")
        page.wait_for_timeout(200)
        check(state["hits"] == hits, tag + " Copy summary after the durable retry does not send")
        page.locator("#sumClose").scroll_into_view_if_needed()
        page.click("#sumClose")
        page.wait_for_timeout(400)
        check(state["hits"] == hits, tag + " Done after the durable retry does not send again")
        print("ACTIONS %s after200 post_after_copy_done=%d" % (tag, state["hits"]))
        ctx.close()

        ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale)
        ctx.add_init_script(INIT)
        ctx.route("**/*", route_all)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        state["hits"] = 0
        page.goto(base + "/exact.html?tab=workout&day=2026-11-06", wait_until="networkidle")
        page.evaluate("() => sessionStorage.setItem('__storageMode','quota')")
        page.reload(wait_until="networkidle")
        target = page.evaluate("""() => {
          const w = W.find(x => x.key !== '2026-11-06|Upper Body' && statusOf(x) === 'planned' && !recordedWindow(x));
          return {key:w.key, date:w.date};
        }""")
        page.goto(base + "/exact.html?tab=workout&day=%s" % target["date"], wait_until="networkidle")
        add = page.locator("[data-addrow]").first
        add.scroll_into_view_if_needed()
        ex_id = add.get_attribute("data-addrow")
        ex = add.locator("xpath=ancestor::div[contains(@class,'ex')][1]")
        before_rows = ex.locator(".srow").count()
        wrong_id = page.evaluate("""() => {
          const rows = [...document.querySelectorAll('.srow')].filter(r => r.querySelector('[data-fw]'));
          const b = rows.length ? rows[rows.length - 1].querySelector('[data-logrow]') : null;
          return b ? b.dataset.logrow : '';
        }""")
        check(bool(ex_id) and wrong_id != ex_id, tag + " negative control: global last editable row is not the clicked Add Set exercise")
        add.click()
        page.wait_for_timeout(200)
        after_rows = ex.locator(".srow").count()
        check(after_rows == before_rows + 1, tag + " Add Set adds one row on the clicked exercise")
        added = ex.locator(".srow").nth(after_rows - 1)
        check(added.locator("[data-logrow]").get_attribute("data-logrow") == ex_id, tag + " the new row belongs to the clicked exercise")
        added.scroll_into_view_if_needed()
        added.locator("[data-fw]").fill("95")
        added.locator("[data-fr]").fill("5")
        added.locator("[data-logrow]").click()
        page.wait_for_timeout(300)
        page.locator("[data-wend]").first.evaluate("el => el.scrollIntoView({block:'center', inline:'nearest'})")
        laid = page.evaluate("""() => {
          function box(sel){
            const el = document.querySelector(sel);
            if (!el) return {ok:false, missing:true};
            const r = el.getBoundingClientRect();
            const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            return {ok: !!(top && (top === el || el.contains(top))), left:r.left, right:r.right, topY:r.top, bottom:r.bottom, vw:innerWidth, vh:innerHeight, inView:r.top >= -1 && r.bottom <= innerHeight + 1};
          }
          const warn = box('#saveRetry');
          const end = box('[data-wend]');
          const timer = box('.timer b');
          const msg = document.getElementById('saveFailMsg');
          const mr = msg.getBoundingClientRect();
          const paint = document.elementFromPoint(mr.left + 12, mr.top + mr.height / 2);
          const separated = warn.bottom <= end.topY || end.bottom <= warn.topY || warn.right <= end.left || end.right <= warn.left;
          return {warn, end, timer, separated, paint: !!(paint && document.getElementById('saveFail').contains(paint))};
        }""")
        check(laid["warn"].get("ok") and laid["warn"].get("inView") and laid["end"].get("ok") and laid["end"].get("inView"), tag + " Retry Save and End Workout are each the top hit")
        check(laid["separated"], tag + " Retry Save does not overlap End Workout")
        check(laid["paint"] and laid["timer"].get("ok"), tag + " the warning is opaque over its own text and the timer is separately reachable")
        nov = page.evaluate("""() => { const w=W.find(x=>x.key==='2026-11-06|Upper Body'); return [w.started_at, w.ended_at]; }""")
        check(nov == WINDOW, tag + " the other workout's new set does not move the Nov 6 recorded window")
        snap(page, tag + "-typed-warning.png", width, height, scale)
        ctx.close()
    browser.close()

httpd.shutdown()
check(sha256(src) == before, "exact HTML bytes unchanged")
if shot_dir:
    import json
    (shot_dir / "capture-hashes.json").write_text(json.dumps({"source_sha256": before, "source_sha256_after": sha256(src), "captures": hashes, "executor": "playwright /usr/bin/google-chrome this session"}, indent=2) + "\n")
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
