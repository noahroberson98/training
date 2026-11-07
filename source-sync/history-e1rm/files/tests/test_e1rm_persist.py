"""Persistence status for an exact sanitized page. Does not rewrite that file.

Usage: python3 tests/test_e1rm_persist.py exact.html [screenshot_dir]

A throwing localStorage.setItem must not be reported as saved. Remote delivery
and local durability are separate. Nothing is sent to a real server.
"""
import hashlib
import shutil
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

UNSAVED = "Not saved on this phone."
SAVED = "Saved on this phone only."
EMAIL_UNSAVED = "Workout emailed. Not saved on this phone."
KEY = "2026-11-06|Upper Body"
WINDOW = ["2026-11-06T15:00:38.635Z", "2026-11-06T15:12:12.324Z"]
INIT = r"""
(() => {
  const orig = Storage.prototype.setItem;
  Storage.prototype.setItem = function (key, value) {
    if (key === "tpDash.logs.v2") {
      let mode = "ok";
      try { mode = sessionStorage.getItem("__storageMode") || "ok"; } catch (e) {}
      if (mode === "quota") throw new DOMException("quota", "QuotaExceededError");
      if (mode === "blocked") throw new DOMException("blocked", "SecurityError");
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

def visible_failure(text):
    return UNSAVED in text and SAVED not in text

check(not visible_failure(SAVED + " Turn on Online sync"), "the old saved-on-phone sentence fails the unsaved check")

if len(sys.argv) < 2:
    print("FAIL exact HTML path required")
    sys.exit(2)
src = Path(sys.argv[1]).resolve()
shot_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
before = sha256(src)
print("BOUND sha256 " + before + " bytes " + str(src.stat().st_size))
check("setTimeout(()=>ac.abort(),12000)" in src.read_text(encoding="utf-8"), "source keeps the 12 second abort")
if shot_dir:
    shot_dir.mkdir(parents=True, exist_ok=True)

serve = Path("/tmp/persist-serve")
if serve.exists():
    shutil.rmtree(serve)
serve.mkdir()
shutil.copy2(src, serve / "exact.html")
check(sha256(src) == before, "copying the page aside did not change the original")

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return
httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(serve)))
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % port

from playwright.sync_api import sync_playwright
CHROME = "/usr/bin/google-chrome"
state = {"mode": "500", "hits": 0, "ext": 0}
hashes = []

def route_all(route):
    url = route.request.url
    if "blocked-outbound" in url:
        state["hits"] += 1
        mode = state["mode"]
        if mode == "500":
            route.fulfill(status=500, content_type="application/json", body='{"success":"false"}')
        elif mode == "200":
            route.fulfill(status=200, content_type="application/json", body='{"success":"true"}')
        elif mode == "throw":
            route.abort("failed")
        elif mode == "hang":
            return
        else:
            route.abort("failed")
        return
    host = url.split("/")[2] if url.startswith("http") else ""
    if host.startswith("127.0.0.1"):
        route.continue_()
    else:
        state["ext"] += 1
        route.abort()

def snap(page, name, w, h, scale):
    if not shot_dir:
        return
    path = shot_dir / name
    page.screenshot(path=str(path))
    doc = page.evaluate("() => document.documentElement.outerHTML")
    box = page.evaluate("() => ({vw:window.innerWidth, vh:window.innerHeight, dpr:window.devicePixelRatio})")
    hashes.append({"name": name, "viewport": [w, h], "device_scale_factor": scale, "measured": box, "png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "png_bytes": path.stat().st_size, "document_sha256": hashlib.sha256(doc.encode()).hexdigest()})

def fresh(browser, w, h, scale, clock=False):
    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=scale)
    ctx.add_init_script(INIT)
    ctx.route("**/*", route_all)
    page = ctx.new_page()
    def on_dialog(d):
        if d.type == "prompt":
            d.accept("95x5")
        else:
            d.accept()
    page.on("dialog", on_dialog)
    if clock:
        page.clock.install()
    return ctx, page

def arm(page, mode):
    page.goto(base + "/exact.html?tab=workout&day=2026-11-06", wait_until="networkidle")
    page.evaluate("(m) => sessionStorage.setItem('__storageMode', m)", mode)
    page.reload(wait_until="networkidle")

def stored_logs(page):
    return page.evaluate("() => localStorage.getItem('tpDash.logs.v2')")

def memory(page):
    return page.evaluate("""() => {
      const w = W.find(x => x.key === '2026-11-06|Upper Body');
      const L = local[w.key] || {};
      const c = sessionTimes(w);
      return {s: w.started_at, e: w.ended_at, eff: [c.started, c.ended], fs: L.fs_sent || null, completed: L.completed_at || null, updated: L.updated_at || null};
    }""")

def visible(page):
    return page.evaluate("""() => ['#sumSync','#saveFail','#syncBadge','#toastMsg'].map(s => {
      const n=document.querySelector(s);
      if(!n || n.hidden || getComputedStyle(n).display==='none') return '';
      return n.innerText;
    }).join('\\n')""")

def six(page):
    return page.evaluate("""() => {
      const w = W.find(x => x.key === '2026-11-06|Upper Body');
      return ['Machine Row','High Incline Press'].flatMap(name => allSets(w, w.exercises.find(e => e.name === name)).filter(s => knownLoadSet(s) && !s.per_plan && !s.round).map(s => [s.weight_lb, s.reps, s.chat_set_id]));
    }""")

SIX = sorted([[105, 7, "t240u#0"], [105, 7, "t240u#1"], [90, 8, "t240u#2"], [30, 13, "t240u#3"], [25, 15, "t240u#4"], [25, 15, "t240u#5"]])

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    ctx, page = fresh(browser, 1280, 900, 1)
    state["hits"] = 0
    state["mode"] = "500"
    arm(page, "quota")
    check(stored_logs(page) in (None, "null", "{}"), "quota mode has not stored a log yet")
    check(state["hits"] == 0 and state["ext"] == 0, "opening the day makes no send and no external request")
    page.click("[data-complete='%s']" % KEY)
    page.wait_for_selector("#sumSync")
    shown = visible(page)
    mem = memory(page)
    check(visible_failure(shown), "quota failure is visible and does not say saved on this phone")
    check(mem["completed"] is not None and mem["updated"] is not None, "summary still updates completed_at and the edit timestamp in memory")
    check([mem["s"], mem["e"]] == WINDOW and mem["eff"] == WINDOW, "recorded workout window stays 11:33 while the summary timestamp changes")
    check(stored_logs(page) in (None, "null", "{}"), "the thrown write did not land in localStorage")
    check("11:33" in page.inner_text("body"), "the recorded duration is still showing")
    page.locator("#sumSync").scroll_into_view_if_needed()
    snap(page, "desktop-summary-storage-failed.png", 1280, 900, 1)
    page.click("#sumClose")
    page.wait_for_timeout(400)
    mid = memory(page)
    check(state["hits"] == 1 and mid["fs"] is None and SAVED not in visible(page), "local 500 does not mark sent and does not claim a local save")
    state["mode"] = "200"
    page.click("#sumClose")
    page.wait_for_timeout(500)
    sent = memory(page)
    toast = page.locator("#toastMsg").inner_text()
    check(state["hits"] == 2 and sent["fs"] and sent["fs"].startswith(KEY + "|"), "local 200 marks sent in this page's memory")
    check(EMAIL_UNSAVED in toast and "Workout emailed ✓" not in toast, "email success names the unsaved sent mark")
    check(stored_logs(page) in (None, "null", "{}"), "the sent mark was not durable while storage threw")
    check(visible_failure(visible(page)), "after delivery the page still says it is not saved")
    snap(page, "desktop-emailed-not-saved.png", 1280, 900, 1)
    if page.locator("#sheet").count():
        page.click("#sumClose")
    else:
        page.click("[data-complete='%s']" % KEY)
        page.wait_for_selector("#sumClose")
        page.click("#sumClose")
    page.wait_for_timeout(400)
    check(state["hits"] == 2, "the same open page does not send again while the sent mark is in memory")
    hits_before_reload = state["hits"]
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(300)
    check(state["hits"] == hits_before_reload, "reload does not send by itself when the sent mark was not stored")
    check(stored_logs(page) in (None, "null", "{}"), "reload still has no durable log")
    page.click("[data-complete='%s']" % KEY)
    page.wait_for_selector("#sumSync")
    check(visible_failure(visible(page)) and state["hits"] == hits_before_reload, "a new summary after reload says not saved and has not sent yet")
    state["mode"] = "200"
    page.click("#sumClose")
    page.wait_for_timeout(400)
    check(state["hits"] == hits_before_reload + 1, "Done after a reload sends again because the sent mark was not durable")
    check([memory(page)["s"], memory(page)["e"]] == WINDOW, "that manual send still leaves the recorded window")
    ctx.close()

    ctx, page = fresh(browser, 390, 844, 2)
    state["hits"] = 0
    state["mode"] = "200"
    arm(page, "quota")
    page.click("[data-complete='%s']" % KEY)
    page.wait_for_selector("#sumSync")
    page.click("#sumClose")
    page.wait_for_timeout(500)
    check(visible_failure(visible(page)) and memory(page)["fs"], "mobile summary shows not saved after a local 200")
    if page.locator("#sumSync").count():
        page.locator("#sumSync").scroll_into_view_if_needed()
    snap(page, "mobile-summary-storage-failed.png", 390, 844, 2)
    has_retry = page.locator("#saveRetry").count() > 0
    check(has_retry, "a retry save control is on the page")
    if has_retry:
        page.evaluate("() => sessionStorage.setItem('__storageMode','ok')")
        if page.locator("#sheet #sumRetry").count():
            page.locator("#sumRetry").scroll_into_view_if_needed()
            page.click("#sumRetry")
        else:
            page.click("#saveRetry")
        page.wait_for_timeout(200)
        raw = stored_logs(page) or ""
        mem = memory(page)
        check(UNSAVED not in visible(page) and "Saved on this phone." in page.locator("#toastMsg").inner_text(), "retry save clears the failure once storage works")
        check(mem["fs"] and mem["fs"] in raw and mem["completed"] in raw, "retry writes the in-memory sent mark and completed_at")
        check(mem["s"] not in (mem["completed"],) and [mem["s"], mem["e"]] == WINDOW, "durable completed_at is not the recorded workout window")
        snap(page, "mobile-save-retried.png", 390, 844, 2)
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(200)
        check(state["hits"] == 1, "reload after a successful retry does not send")
        page.click("[data-complete='%s']" % KEY)
        page.wait_for_selector("#sumClose")
        shown = visible(page)
        check(SAVED in shown and UNSAVED not in shown, "after a durable save the summary can say saved on this phone")
        page.click("#sumClose")
        page.wait_for_timeout(400)
        check(state["hits"] == 1 and memory(page)["fs"] == mem["fs"], "Done after the durable retry does not send again")
        check([memory(page)["s"], memory(page)["e"]] == WINDOW and "11:33" in page.inner_text("body"), "recorded 11:33 remains after retry, reload, and a second summary")
    ctx.close()

    ctx, page = fresh(browser, 1280, 900, 1)
    state["hits"] = 0
    state["mode"] = "200"
    arm(page, "ok")
    target = page.evaluate("""() => {
      const w = W.find(x => x.key !== '2026-11-06|Upper Body' && statusOf(x) === 'planned' && !recordedWindow(x) && working(x).length);
      return w ? {key: w.key, date: w.date} : null;
    }""")
    check(bool(target) and target["key"] != KEY, "an isolated planned workout is available for a new typed set")
    page.goto(base + "/exact.html?tab=workout&day=%s" % target["date"], wait_until="networkidle")
    quick = page.evaluate("""() => {
      const b = document.querySelector('[data-quicklog]');
      if (!b) return null;
      const box = b.closest('.now');
      return {id: b.dataset.quicklog, w: box.querySelector('[data-qw]').value, r: box.querySelector('[data-qr]').value};
    }""")
    check(bool(quick) and quick["id"].startswith(target["key"] + "::"), "the quick-log path is the first empty set on that workout")
    page.click("[data-quicklog]")
    page.wait_for_timeout(300)
    row = page.locator(".srow").filter(has=page.locator("[data-fw]")).first
    row.scroll_into_view_if_needed()
    row.locator("[data-fw]").fill("80")
    row.locator("[data-fr]").fill("4")
    row.locator("[data-logrow]").click()
    page.wait_for_timeout(300)
    page.locator("[data-addrow]").first.click()
    page.wait_for_timeout(300)
    added = page.locator(".srow").filter(has=page.locator("[data-fw]")).last
    added.scroll_into_view_if_needed()
    added.locator("[data-fw]").fill("95")
    added.locator("[data-fr]").fill("5")
    added.locator("[data-logrow]").click()
    page.wait_for_timeout(300)
    typed = page.evaluate("""(id) => {
      const k = id.slice(0, id.indexOf('::'));
      const sets = Object.values((local[k] || {}).exercises || {}).flatMap(x => x.sets || []);
      const raw = localStorage.getItem('tpDash.logs.v2') || '';
      const nov = local['2026-11-06|Upper Body'] || null;
      return {sets, rawHas: raw.indexOf('95') >= 0, nov, started: (local[k] || {}).started_at || null};
    }""", quick["id"])
    def same_weight(s, raw):
        if raw == "":
            return s.get("weight_lb") is None
        try:
            return abs(float(s.get("weight_lb")) - float(raw)) < 1e-6
        except (TypeError, ValueError):
            return False
    check(any(same_weight(s, quick["w"]) for s in typed["sets"]), "quick log kept the typed weight in memory")
    check(any(s.get("weight_lb") == 80 and s.get("reps") == 4 for s in typed["sets"]), "the row inputs logged 80×4")
    check(any(s.get("weight_lb") == 95 and s.get("reps") == 5 for s in typed["sets"]), "the rendered Add Set row kept 95×5")
    check(typed["rawHas"] and "95" in (stored_logs(page) or ""), "both new sets were written through localStorage")
    check(typed["nov"] is None, "the new sets were not written onto the Nov 6 workout")
    check(sorted(six(page)) == SIX, "the supplied six source sets stay single")
    check(typed["started"] is not None, "the first typed set on a workout with no recorded window starts a local clock")
    nov = memory(page)
    check([nov["s"], nov["e"]] == WINDOW and nov["eff"] == WINDOW, "that new clock is not the Nov 6 recorded window")
    page.reload(wait_until="networkidle")
    kept = page.evaluate("""(id) => {
      const k = id.slice(0, id.indexOf('::'));
      const sets = Object.values((local[k] || {}).exercises || {}).flatMap(x => x.sets || []);
      return sets.some(s => s.weight_lb == 95 && s.reps == 5);
    }""", quick["id"])
    check(kept and sorted(six(page)) == SIX, "reload keeps the new sets and the six source sets")
    snap(page, "desktop-first-typed-set.png", 1280, 900, 1)
    ctx.close()

    ctx, page = fresh(browser, 390, 844, 2)
    state["mode"] = "200"
    arm(page, "blocked")
    target = page.evaluate("""() => {
      const w = W.find(x => x.key !== '2026-11-06|Upper Body' && statusOf(x) === 'planned' && !recordedWindow(x));
      return {key: w.key, date: w.date};
    }""")
    page.goto(base + "/exact.html?tab=workout&day=%s" % target["date"], wait_until="networkidle")
    page.click("[data-quicklog]")
    page.wait_for_timeout(200)
    blocked = page.evaluate("""() => {
      const id = Object.keys(local).find(k => !k.startsWith('_') && local[k] && local[k].exercises);
      const raw = localStorage.getItem('tpDash.logs.v2');
      return {id, raw, text: document.getElementById('saveFail') ? document.getElementById('saveFail').innerText : ''};
    }""")
    check(blocked["id"] == target["key"] and blocked["raw"] in (None, "null", "{}"), "a blocked write keeps the typed set in memory only")
    check(visible_failure(blocked["text"] or visible(page)), "blocked storage shows not saved")
    check(sorted(six(page)) == SIX and [memory(page)["s"], memory(page)["e"]] == WINDOW, "blocked typing leaves the Nov 6 source and recorded window")
    snap(page, "mobile-typed-set-not-saved.png", 390, 844, 2)
    if page.locator("#saveRetry").count():
        page.evaluate("() => sessionStorage.setItem('__storageMode','ok')")
        page.click("#saveRetry")
        page.wait_for_timeout(200)
        raw = stored_logs(page) or ""
        check(target["key"] in raw and UNSAVED not in visible(page), "retry after unblocking stores the typed set")
        page.reload(wait_until="networkidle")
        still = page.evaluate("(k) => !!(local[k] && local[k].exercises)", target["key"])
        check(still, "reload after retry still has the typed set")
    ctx.close()

    ctx, page = fresh(browser, 1280, 900, 1)
    state["hits"] = 0
    state["mode"] = "throw"
    arm(page, "ok")
    page.click("[data-complete='%s']" % KEY)
    page.wait_for_selector("#sumClose")
    page.click("#sumClose")
    page.wait_for_timeout(400)
    thrown = memory(page)
    check(state["hits"] == 1 and thrown["fs"] is None and "Email failed" in page.locator("#toastMsg").inner_text(), "a thrown request does not mark sent")
    check([thrown["s"], thrown["e"]] == WINDOW and thrown["completed"] is not None, "a thrown request leaves the recorded window and still has completed_at")
    ctx.close()

    ctx, page = fresh(browser, 1280, 900, 1)
    state["hits"] = 0
    state["mode"] = "hang"
    arm(page, "ok")
    page.click("[data-complete='%s']" % KEY)
    page.wait_for_selector("#sumClose")
    page.click("#sumClose")
    started = time.monotonic()
    page.wait_for_function("() => (document.getElementById('toastMsg') || {}).textContent.indexOf('Email failed') >= 0", timeout=20000)
    elapsed = time.monotonic() - started
    aborted = memory(page)
    print("ABORT_SECONDS %.2f" % elapsed)
    check(state["hits"] == 1 and aborted["fs"] is None and "Email failed" in page.locator("#toastMsg").inner_text() and elapsed >= 11, "the 12 second abort does not mark sent")
    check([aborted["s"], aborted["e"]] == WINDOW, "the abort leaves the recorded window")
    ctx.close()

    check(state["ext"] == 0, "no external request was allowed")
    browser.close()

httpd.shutdown()
check(sha256(src) == before, "exact HTML bytes unchanged after the browser run")
if shot_dir:
    (shot_dir / "capture-hashes.json").write_text(__import__("json").dumps({"source_sha256": before, "source_sha256_after": sha256(src), "captures": hashes, "executor": "playwright chromium /usr/bin/google-chrome", "note": "PNGs were written by this process from the page path above. A matching hash with an older file is not a freshness claim."}, indent=2) + "\n")
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
