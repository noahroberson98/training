"""Mobile Hide and Undo on the template-generated page. Not the standalone demo."""
import json
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import assemble_fixture  # noqa: E402

assemble_fixture.main()
ok = True
proof = []


def check(cond, name, expected, actual):
    global ok
    row = {"check": name, "expected": expected, "actual": actual, "pass": bool(cond)}
    proof.append(row)
    print(("PASS " if cond else "FAIL ") + name)
    print("  expected: " + json.dumps(expected, ensure_ascii=False))
    print("  actual:   " + json.dumps(actual, ensure_ascii=False))
    ok = ok and bool(cond)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return


httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(HERE / "assembled")))
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
from playwright.sync_api import sync_playwright

shots = HERE / "shots"
shots.mkdir(exist_ok=True)
INIT = r"""
(() => {
  const orig = Storage.prototype.setItem;
  Storage.prototype.setItem = function (k, v) {
    if (window.__failStorage && k === "tpDash.classHide.v1") throw new DOMException("quota", "QuotaExceededError");
    return orig.call(this, k, v);
  };
})();
"""
blocked = []
APEX = "2099-01-01|10:00|APEX"
MISSING = "2099-01-02|10:00|APEX"
OTHER = "2099-01-03|09:00|THIS STRENGTH"
SENTENCE = "You reported this cancelled. The gym list still says reserved."
FAIL = "Not saved on this phone. The class is still listed."
SCOPE = "This phone remembers Hide and Undo in this browser. It does not write user_overrides.json and it does not change another device. A rebuilt page hides a class when that file says hidden."


def card(page, key, root):
    return page.locator(f"{root} [data-key='{key}']")


def attrs(page, key, root="#hidden"):
    loc = card(page, key, root).first
    return loc.evaluate("""el => ({
      status: el.dataset.status, csv: el.dataset.csv, source: el.dataset.source,
      cancel: el.dataset.cancelSource, provider: el.dataset.provider,
      store: el.dataset.hideStore, hidden: el.dataset.hidden,
      undo: (el.querySelector("[data-undocls]")||{}).textContent || "",
      hide: (el.querySelector("[data-hidecls]")||{}).textContent || "",
      text: el.innerText
    })""")


def open_day(page, name, day, tab="workout"):
    page.goto(f"http://127.0.0.1:{port}/{name}.html?tab={tab}&day={day}", wait_until="domcontentloaded")
    page.wait_for_selector("#main")
    if tab != "history":
        page.wait_for_selector("#classHide")


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    ctx.add_init_script(INIT)
    def route(r):
        if r.request.url.startswith("http://127.0.0.1"):
            r.continue_()
        else:
            blocked.append(r.request.url)
            r.abort()
    ctx.route("**/*", route)
    page = ctx.new_page()
    errors = []
    dialogs = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    open_day(page, "current", "2099-01-03")
    check(card(page, OTHER, "#booked").count() == 1, "other booking listed", 1, card(page, OTHER, "#booked").count())
    check(card(page, APEX, "#hidden").count() == 1 and card(page, MISSING, "#hidden").count() == 1, "baked hides are in Hidden By You", [APEX, MISSING], [APEX, MISSING])
    baked = attrs(page, APEX)
    check(baked["status"] == "CANCELLED" and baked["csv"] == "RESERVED" and baked["source"] == "synthetic feed" and baked["cancel"] == "user" and baked["provider"] == "false" and baked["store"] == "built" and SENTENCE in baked["text"] and baked["undo"].strip() == "Undo", "stale reserved row keeps user-cancel provenance", {"status": "CANCELLED", "csv": "RESERVED", "cancel": "user", "provider": "false", "store": "built"}, baked)
    missing = attrs(page, MISSING)
    check(missing["status"] == "CANCELLED" and missing["status"] != "COMPLETED" and missing["csv"] == "RESERVED" and missing["provider"] == "false", "missing feed row is hidden and not completed", "CANCELLED/RESERVED/false", {"status": missing["status"], "csv": missing["csv"], "provider": missing["provider"]})
    check(page.locator("#hideScope").inner_text() == SCOPE, "persistence boundary is on the page", SCOPE, page.locator("#hideScope").inner_text())
    page.screenshot(path=str(shots / "mobile-before.png"), full_page=True)

    open_day(page, "current", "2099-01-01")
    row_text = page.locator("#main").inner_text()
    check("40 lb × 8" in row_text and "Skipped" in row_text and "Row" in row_text, "user-cancelled workout keeps its set", "Row 40 lb × 8 and Skipped", row_text)
    open_day(page, "current", "2099-01-03")
    locked = page.locator("[data-wkey='2099-01-03|Strength']")
    main3 = page.locator("#main").inner_text()
    locked_meta = locked.evaluate("el => ({locked: el.dataset.locked, status: el.dataset.storeStatus})")
    locked_meta["text"] = main3
    check(locked_meta["locked"] == "true" and locked_meta["status"] == "completed" and "185 lb × 5" in main3 and "Completed" in main3 and "Squat" in main3, "locked workout status and set stay", {"locked": "true", "status": "completed", "set": "185 lb × 5"}, locked_meta)
    open_day(page, "current", "2099-01-06")
    upper = page.locator("#main").inner_text()
    warm = page.locator("details.warm").text_content() or ""
    check("Bench Press" in upper and "135 lb × 8" in upper and "145 lb × 6" in upper and "Personal Training" in upper and "Easy Bike" in warm, "upper body session and PT resume stay", "Bench Press, 135 lb × 8, Personal Training, Easy Bike", {"visible": upper, "warm": warm})

    open_day(page, "current", "2099-01-03")
    before_keys = page.locator("[data-key]").evaluate_all("els => els.map(e => e.dataset.key)")
    card(page, OTHER, "#booked").locator("[data-hidecls]").click()
    check(card(page, OTHER, "#booked").count() == 0 and card(page, OTHER, "#hidden").count() == 1, "hide moves that booking under Hidden By You", "hidden", "hidden" if card(page, OTHER, "#hidden").count() else "still booked")
    check(card(page, OTHER, "#hidden").locator("[data-undocls]").inner_text() == "Undo", "undo is on the hidden row", "Undo", card(page, OTHER, "#hidden").locator("[data-undocls]").inner_text())
    check(card(page, APEX, "#hidden").count() == 1 and card(page, MISSING, "#hidden").count() == 1, "other hidden rows stay", 2, card(page, APEX, "#hidden").count() + card(page, MISSING, "#hidden").count())
    page.screenshot(path=str(shots / "mobile-hidden.png"), full_page=True)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#classHide")
    stored = page.evaluate("() => localStorage.getItem('tpDash.classHide.v1')")
    check(card(page, OTHER, "#hidden").count() == 1 and OTHER in (stored or ""), "hide survives reload in this browser", OTHER, stored)
    card(page, OTHER, "#hidden").locator("[data-undocls]").click()
    check(card(page, OTHER, "#booked").count() == 1 and card(page, OTHER, "#hidden").count() == 0, "undo puts the booking back on this day", "booked", "booked" if card(page, OTHER, "#booked").count() else "hidden")
    page.screenshot(path=str(shots / "mobile-undo.png"), full_page=True)

    page.evaluate("() => { window.__failStorage = true; }")
    card(page, OTHER, "#booked").locator("[data-hidecls]").click()
    warn = page.locator("#classHideWarn").inner_text() if page.locator("#classHideWarn").count() else ""
    still = card(page, OTHER, "#booked").count()
    main_after = page.locator("#main").inner_text()
    check(warn == FAIL and still == 1 and "185 lb × 5" in main_after and "Completed" in main_after, "failed save leaves the class listed", {"warn": FAIL, "booked": 1, "set": "185 lb × 5"}, {"warn": warn, "booked": still, "set": "185 lb × 5" in main_after})
    page.screenshot(path=str(shots / "mobile-save-failed.png"), full_page=True)
    page.evaluate("() => { window.__failStorage = false; }")

    card(page, APEX, "#hidden").locator("[data-undocls]").click()
    phone = attrs(page, APEX, "#hidden") if card(page, APEX, "#hidden").count() else {}
    open_day(page, "current", "2099-01-01")
    shown = attrs(page, APEX, "#booked")
    sets_after = "40 lb × 8" in page.locator("#main").inner_text()
    check(shown["hidden"] == "false" and shown["store"] == "phone" and shown["status"] == "CANCELLED" and shown["csv"] == "RESERVED" and shown["cancel"] == "user" and shown["provider"] == "false" and SENTENCE in shown["text"] and sets_after, "undo changes visibility only", {"hidden": "false", "store": "phone", "status": "CANCELLED", "provider": "false", "set": True}, {"card": shown, "set": sets_after})
    card(page, APEX, "#booked").locator("[data-hidecls]").click()
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#hidden")
    check(card(page, APEX, "#hidden").count() == 1, "phone hide of the undone row survives reload", 1, card(page, APEX, "#hidden").count())

    open_day(page, "reimport-reserved", "2099-01-03")
    same = attrs(page, APEX)
    check(same["hidden"] == "true" and same["store"] == "phone" and same["csv"] == "RESERVED", "same browser keeps the phone hide across a rebuilt reserved feed", "phone/hidden/RESERVED", same)
    check(card(page, OTHER, "#booked").count() == 1, "rebuilt page does not hide the other booking", 1, card(page, OTHER, "#booked").count())

    fresh = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    fresh.add_init_script(INIT)
    fresh.route("**/*", route)
    page2 = fresh.new_page()
    page2.on("pageerror", lambda e: errors.append(str(e)))
    open_day(page2, "reimport-reserved", "2099-01-03")
    bare = page2.evaluate("() => localStorage.getItem('tpDash.classHide.v1')")
    again = attrs(page2, APEX)
    check(bare in (None, "null") and again["store"] == "built" and again["status"] == "CANCELLED" and again["csv"] == "RESERVED" and again["provider"] == "false", "empty browser still hides the stale reserved row from the override file", "built/CANCELLED/RESERVED", {"storage": bare, "card": again})
    open_day(page2, "reimport-missing", "2099-01-03")
    gone = attrs(page2, MISSING)
    gone1 = attrs(page2, APEX)
    check(gone["status"] == "CANCELLED" and gone["status"] != "COMPLETED" and gone1["status"] != "COMPLETED" and card(page2, OTHER, "#booked").count() == 1, "missing rows stay hidden and not completed", "CANCELLED not COMPLETED", {"missing": gone["status"], "stale": gone1["status"], "other": card(page2, OTHER, "#booked").count()})

    open_day(page2, "current", "2099-01-06", "history")
    page2.wait_for_selector("#ex-bench-press")
    names = page2.locator("#ex-pick option").all_inner_texts()
    page2.locator("#ex-bench-press [data-hist]").click()
    page2.wait_for_selector("#ex-bench-press .hdetail.on")
    hist = page2.locator("#ex-bench-press").inner_text()
    check("Bench Press" in names and "Row" in names and "Squat" in names and "135" in hist, "history still lists the logged exercises", ["Bench Press", "Row", "Squat", "135"], {"names": names, "detail": hist})
    open_day(page2, "current", "2099-01-03", "week")
    page2.wait_for_selector(".cc[data-key='2099-01-03|09:00|THIS STRENGTH']")
    week_locked = page2.locator(".cc[data-key='2099-01-03|09:00|THIS STRENGTH'] .lock").count()
    page2.locator(".cc[data-key='2099-01-03|09:00|THIS STRENGTH'] [data-hidecls]").click()
    check(week_locked == 1 and card(page2, OTHER, "#hidden").count() == 1 and page2.locator(".cc[data-key='2099-01-03|09:00|THIS STRENGTH']").count() == 0, "week card stays locked and Hide removes it from the week column", "locked then hidden", {"lock": week_locked, "hidden": card(page2, OTHER, "#hidden").count()})
    after_keys = page.locator("[data-key]").evaluate_all("els => els.map(e => e.dataset.key).sort()")
    check(sorted(set(before_keys)) == sorted(set(before_keys) | {APEX, MISSING, OTHER}) or set(before_keys) >= {APEX, MISSING, OTHER}, "row identity before hide", [APEX, MISSING, OTHER], before_keys)
    check(errors == [] and blocked == [] and dialogs == [], "no page error, dialog, or off-machine request", [], {"errors": errors, "blocked": blocked, "dialogs": dialogs})
    fresh.close()
    browser.close()

httpd.shutdown()
(HERE / "logs").mkdir(exist_ok=True)
(HERE / "logs" / "template-mobile.json").write_text(json.dumps({"pass": ok, "checks": proof, "blocked": blocked, "errors": errors}, indent=2) + "\n")
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
