"""Browser proof for an exact sanitized History page. Does not rewrite that file.

Usage: python3 tests/test_e1rm_exact.py exact.html [screenshot_dir]

The build clock and title are read from the file. A hardcoded older snapshot
clock is not required. HTTP(S) except this process's local server is aborted.
Finish is answered with a local 500, then a local 200. Nothing is delivered.
"""
import hashlib, math, os, re, shutil, sys, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial

CLOCK_RE = re.compile(r"built ([A-Z][a-z]{2} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M CT)")

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def build_clocks(html):
    return CLOCK_RE.findall(html)

def clock_claim_ok(html):
    if "current-data-preview" in html:
        return False
    return len(build_clocks(html)) >= 1

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
html = src.read_text(encoding="utf-8")
check(before == sha256(src), "hash read did not change the file")
print("BOUND sha256 " + before + " bytes " + str(src.stat().st_size))
clocks = build_clocks(html)
check(clock_claim_ok(html), "file carries its own build clock")
check(not clock_claim_ok("built current-data-preview"), "debug build slug fails the clock check")
check(not clock_claim_ok(html.replace(clocks[0], "current-data-preview", 1)), "swapping the clock for the debug slug fails")
falsified = html.replace(clocks[0], "Jan 1, 1999 1:00 AM CT", 1)
check(build_clocks(falsified) == ["Jan 1, 1999 1:00 AM CT"] and build_clocks(falsified) != clocks, "a substituted clock is not this file's clock")
check('const FS_TOKEN=""' in html and "formsubmit.co" not in html and "api.github.com" not in html, "safe page has an empty token and blocked hosts")
check("/*RELAY*/" not in html, "dormant cancellation relay is not in this page")
check(all(("t240u#%d" % i) in html for i in range(6)), "six chat set ids remain")

if shot_dir:
    shot_dir.mkdir(parents=True, exist_ok=True)

serve = Path("/tmp/exact-serve")
if serve.exists():
    shutil.rmtree(serve)
serve.mkdir()
shutil.copy2(src, serve / "exact.html")
open(serve / "open.html", "w", encoding="utf-8").write("""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Local embed only — not live JARVIS</title>
<style>body{margin:0;background:#111;color:#eee;font:15px/1.45 sans-serif}header,section{padding:16px 20px}header{background:#222}iframe{width:100%;height:900px;border:0;background:#000}</style>
</head><body>
<header><strong>Local embed only.</strong> Not live JARVIS. Not a release. This frame loads the exact sanitized page on this origin.</header>
<section><iframe title="Local training history" src="exact.html?tab=history&amp;ex=machine-row"></iframe></section>
</body></html>
""")
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
        if state["mode"] == "500":
            route.fulfill(status=500, content_type="application/json", body='{"success":"false"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"success":"true"}')
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

SOURCE_POINTS = [
    ("Machine Row", "2026-10-30", 90, 13),
    ("Machine Row", "2026-11-06", 105, 7),
    ("High Incline Press", "2026-10-30", 40, 8),
    ("High Incline Press", "2026-11-06", 30, 13),
    ("Plate Loaded Lat Pull Down", "2026-10-21", 180, 10),
    ("Plate Loaded Lat Pull Down", "2026-10-30", 280, 6),
    ("Machine Chest Fly", "2026-10-30", 105, 15),
    ("DB Incline Lateral Raise", "2026-10-30", 10, 10),
    ("DB Incline Curl", "2026-10-21", 15, 15),
    ("DB Incline Curl", "2026-10-30", 17.5, 8),
    ("Cable Rope Curl", "2026-10-21", 35, 12),
    ("Cable Rope Tricep Push Down", "2026-10-21", 35, 17),
    ("Barbell RDL", "2026-10-25", 155, 8),
]

def expect_estimate(weight, reps):
    if reps == 1:
        return weight, None, "actual_single", "actual"
    primary = weight * (1 + reps / 30.0)
    brzycki = weight * 36.0 / (37.0 - reps) if 2 <= reps <= 10 else None
    return primary, brzycki, "epley", ("low" if reps > 12 else "estimate")

def near(a, b):
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-6)

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    def fresh(w, h, scale):
        ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=scale)
        ctx.route("**/*", route_all)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page._errs = errs
        return ctx, page

    ctx, page = fresh(390, 844, 2)
    page.goto(base + "/exact.html?tab=history&ex=machine-row", wait_until="networkidle")
    page.wait_for_selector("#e1rm-panel")
    menu = page.locator(".meta").inner_text()
    check(clocks[0] in menu, "menu shows this file's build clock")
    check("current-data-preview" not in menu, "menu is not the debug slug")
    text = page.inner_text("#e1rm-panel")
    check("Failure/effort status is not consistently recorded or independently verified." in text, "effort caveat")
    check("does not say a set was to failure" not in text, "old effort caveat is absent")
    check("fail" not in page.locator("[data-e1rm-latest]").inner_text().lower(), "latest session is not called a failure")
    check("Pounds assumed" in text and "2026" in text and "Nov 6, 2026" in text, "assumed pounds and full date")
    check("Best Estimates" in page.locator("#aside").inner_text() and "Logged Only" in page.inner_text("body"), "Title Case")
    style = page.evaluate("""()=>{const th=document.querySelector('.e1rm-table th.num'); const td=document.querySelector('.e1rm-table td.num'); return {tf:getComputedStyle(th).textTransform, al:getComputedStyle(td).textAlign};}""")
    check(style["tf"] == "none" and style["al"] == "right", "numeric columns align right without forced uppercase")
    tips = page.eval_on_selector_all("#e1rm-panel svg title", "els => els.map(e => e.textContent)")
    check(len(tips) == 2 and all("2026" in t and "×" in t and "Epley" in t for t in tips), "row tooltips")
    page.locator("#e1rm-panel .e1rm-pt").nth(1).dispatch_event("mouseover")
    check(page.locator("#e1rm-tip").inner_text() == tips[1], "active tooltip matches the Nov 6 title")
    snap(page, "mobile-history-populated-tooltip.png", 390, 844, 2)
    page.select_option("#ex-pick", "abmat-sit-up")
    page.wait_for_selector("[data-e1rm-state=empty]")
    check("No estimated max" in page.inner_text("#e1rm-panel"), "AbMat has no estimate")
    snap(page, "mobile-history-empty.png", 390, 844, 2)
    page.select_option("#ex-pick", "machine-row")
    page.fill("#hq", "row")
    check(page.evaluate("localStorage.getItem('tpDash.logs.v2')") is None, "search and selection wrote no log")
    points = page.evaluate("""()=>{
      const out=[];
      sessions().forEach(s=>{
        const series=e1rmSeries(e1rmItems(s));
        series.points.forEach(pt=>out.push({name:s.name, date:pt.date, w:pt.topWeight, r:pt.topReps, primary:pt.primary, brz:pt.brzycki, method:pt.method, conf:pt.confidence, basis:pt.basis}));
        if(!series.points.length) out.push({name:s.name, empty:true});
      });
      return out;
    }""")
    got = [(p["name"], p["date"], p["w"], p["r"]) for p in points if not p.get("empty")]
    check(got == SOURCE_POINTS, "thirteen source-bound top sets")
    formula_ok = True
    for p in points:
        if p.get("empty"):
            continue
        primary, brz, method, conf = expect_estimate(p["w"], p["r"])
        formula_ok = formula_ok and p["method"] == method and p["conf"] == conf and near(p["primary"], primary) and near(p["brz"], brz)
    check(formula_ok, "each point matches Epley, with Brzycki only for 2–10 reps")
    db = [p for p in points if str(p["name"]).startswith("DB ")]
    check(db and all(p["basis"] == "per_hand_unconfirmed" and p["w"] < 20 for p in db), "dumbbell loads stay per hand and are not doubled")
    incline = next(p for p in points if p["name"] == "High Incline Press" and p["date"] == "2026-11-06")
    check(incline["w"] == 30 and near(incline["primary"], 43) and incline["primary"] != 86, "incline 30×13 is not doubled")
    check(any(p.get("name") == "AbMat Sit Up" and p.get("empty") for p in points), "AbMat has no estimate point")
    snap(page, "mobile-history-populated.png", 390, 844, 2)
    ctx.close()

    ctx, page = fresh(1280, 900, 1)
    page.goto(base + "/exact.html?tab=history&ex=machine-row", wait_until="networkidle")
    page.wait_for_selector("#e1rm-panel")
    snap(page, "desktop-history-populated.png", 1280, 900, 1)
    page.click("#gear")
    page.wait_for_selector("#menu.on")
    check(clocks[0] in page.locator(".meta").inner_text(), "open menu shows the build clock")
    snap(page, "desktop-menu.png", 1280, 900, 1)
    page.keyboard.press("Escape")
    page.select_option("#ex-pick", "abmat-sit-up")
    snap(page, "desktop-history-empty.png", 1280, 900, 1)
    ctx.close()

    ctx, page = fresh(390, 844, 2)
    page.goto(base + "/exact.html?tab=workout&day=2026-11-06", wait_until="networkidle")
    day = page.evaluate("""()=>{
      const w=W.find(x=>x.key==='2026-11-06|Upper Body');
      const pr=progress(w); const c=sessionTimes(w);
      const sets=['Machine Row','High Incline Press'].flatMap(name=>allSets(w,w.exercises.find(e=>e.name===name)).filter(s=>knownLoadSet(s)&&!s.per_plan&&!s.round).map(s=>[s.weight_lb,s.reps,s.chat_set_id]));
      return {logged:pr.logged, planned:pr.planned, st:statusOf(w), s:w.started_at, e:w.ended_at, effS:c.started, effE:c.ended, tick:document.querySelectorAll('[data-tick]').length, end:document.querySelectorAll('[data-wend]').length, time:(document.body.innerText.match(/Workout time\\s+[0-9:]+/)||[''])[0], sets};
    }""")
    check(day["logged"] == 6 and day["planned"] == 27 and day["st"] == "completed", "day is 6 logged of 27 planned and completed")
    check(day["s"] == "2026-11-06T15:00:38.635Z" and day["e"] == "2026-11-06T15:12:12.324Z" and day["time"] == "Workout time 11:33", "recorded 11:33 window is showing")
    print("RECORDED " + day["time"])
    check(day["tick"] == 0 and day["end"] == 0, "no live clock before a click")
    check(sorted(day["sets"]) == sorted([[105,7,"t240u#0"],[105,7,"t240u#1"],[90,8,"t240u#2"],[30,13,"t240u#3"],[25,15,"t240u#4"],[25,15,"t240u#5"]]), "six logged sets stay single, not doubled")
    snap(page, "mobile-day.png", 390, 844, 2)
    page.locator(".timer").first.scroll_into_view_if_needed()
    snap(page, "mobile-day-clock.png", 390, 844, 2)
    page.reload(); page.wait_for_timeout(300)
    check("11:33" in page.inner_text("body") and page.evaluate("()=>W.find(x=>x.key==='2026-11-06|Upper Body').started_at")==day["s"], "reload keeps the recorded window")
    ctx.close()

    ctx, page = fresh(1280, 900, 1)
    page.goto(base + "/exact.html?tab=workout&day=2026-11-06", wait_until="networkidle")
    aside = page.locator("#aside").inner_text()
    check("Known-load volume 3,330 lb · 6 of 30 logged sets with recorded loads · 24 sets without recorded loads" in aside, "day sidebar shows this week's known-load volume")
    snap(page, "desktop-day.png", 1280, 900, 1)
    page.locator(".timer").first.scroll_into_view_if_needed()
    snap(page, "desktop-day-clock.png", 1280, 900, 1)
    page.goto(base + "/exact.html?tab=week&day=2026-11-06", wait_until="networkidle")
    week = page.evaluate("""()=>{
      const wk=W.filter(w=>wkStart(w.date)===wkStart('2026-11-06'));
      const f=weekLoadFacts(wk);
      const text=weekVolumeText(f);
      const cards=document.querySelector('[data-dropday="2026-11-06"]').innerText;
      return {logged:f.logged, planned:f.planned, known:f.known, missing:f.missing, lvol:f.lvol, text, cards, n:document.querySelectorAll('[data-dropday="2026-11-06"] .wc').length, aside:document.getElementById('aside').innerText};
    }""")
    check(week["n"] == 1 and "Personal Training" in week["cards"] and "9:00 AM CT" in week["cards"], "one completed Personal Training Upper Body card")
    check(week["logged"] == 30 and week["lvol"] == 3330 and week["known"] == 6 and week["missing"] == 24 and week["text"] == "Known-load volume 3,330 lb · 6 of 30 logged sets with recorded loads · 24 sets without recorded loads", "week known-load volume is 3330 from 6 of 30, 24 missing")
    check(week["aside"] == "", "week view hides the sidebar instead of repeating it")
    snap(page, "desktop-week.png", 1280, 900, 1)
    page.click("[data-wk='-7']")
    page.wait_for_timeout(200)
    other = page.evaluate("""()=>{
      const wk=W.filter(w=>wkStart(w.date)===wkStart(sel));
      const f=weekLoadFacts(wk);
      return {text:weekVolumeText(f), lvol:f.lvol};
    }""")
    check(other["text"] != week["text"] and other["lvol"] != 3330, "another week does not repeat this week's volume")
    snap(page, "desktop-week-other.png", 1280, 900, 1)
    ctx.close()

    ctx, page = fresh(390, 844, 2)
    page.goto(base + "/exact.html?tab=week&day=2026-11-06", wait_until="networkidle")
    snap(page, "mobile-week.png", 390, 844, 2)
    ctx.close()

    ctx, page = fresh(390, 844, 2)
    page.goto(base + "/exact.html?tab=workout&day=2026-11-06", wait_until="networkidle")
    before_clock = page.evaluate("()=>{const w=W.find(x=>x.key==='2026-11-06|Upper Body'); return [w.started_at, w.ended_at];}")
    check(state["hits"] == 0, "history and navigation made no send request")
    page.click("[data-complete='2026-11-06|Upper Body']")
    page.wait_for_selector("#sumClose")
    page.click("#sumClose")
    page.wait_for_function("() => { const b=document.getElementById('sumClose'); return b && !b.disabled && b.textContent==='Done'; }")
    mid = page.evaluate("()=>{const w=W.find(x=>x.key==='2026-11-06|Upper Body'); const L=local[w.key]||{}; const c=sessionTimes(w); return {s:w.started_at, e:w.ended_at, fs:L.fs_sent||null, eff:[c.started,c.ended]};}")
    check(state["hits"] == 1 and mid["fs"] is None and [mid["s"], mid["e"]] == before_clock and mid["eff"] == before_clock, "local 500 does not mark sent or move the recorded clock")
    state["mode"] = "200"
    page.click("#sumClose")
    page.wait_for_selector("#sheet", state="detached")
    sent = page.evaluate("()=>{const w=W.find(x=>x.key==='2026-11-06|Upper Body'); const L=local[w.key]||{}; const c=sessionTimes(w); return {s:w.started_at, e:w.ended_at, fs:L.fs_sent||'', eff:[c.started,c.ended]};}")
    check(state["hits"] == 2 and sent["fs"].startswith("2026-11-06|Upper Body|") and [sent["s"], sent["e"]] == before_clock and sent["eff"] == before_clock, "local 200 sets fs_sent and leaves the recorded clock")
    page.click("[data-complete='2026-11-06|Upper Body']")
    page.wait_for_selector("#sumClose")
    page.click("#sumClose")
    page.wait_for_selector("#sheet", state="detached")
    again = page.evaluate("()=>{const w=W.find(x=>x.key==='2026-11-06|Upper Body'); const c=sessionTimes(w); return [w.started_at, w.ended_at, (local[w.key]||{}).fs_sent||'', c.started, c.ended];}")
    shown = page.inner_text("body")
    check(state["hits"] == 2 and again[0] == before_clock[0] and again[1] == before_clock[1] and again[2] == sent["fs"] and again[3] == before_clock[0] and again[4] == before_clock[1] and "11:33" in shown, "a second summary does not send again or move timestamps")
    check(state["ext"] == 0 and not page._errs, "no external request and no page error")
    ctx.close()

    ctx, page = fresh(1280, 900, 1)
    page.goto(base + "/open.html", wait_until="networkidle")
    page.evaluate("window.scrollTo(0,0)")
    check("Not live JARVIS" in page.inner_text("header"), "iframe page says it is local only")
    snap(page, "local-iframe.png", 1280, 900, 1)
    ctx.close()
    browser.close()

httpd.shutdown()
after = sha256(src)
check(after == before, "exact HTML bytes unchanged after the browser run")
if shot_dir:
    (shot_dir / "capture-hashes.json").write_text(__import__("json").dumps({"source_sha256": before, "source_sha256_after": after, "build_clock": clocks[0], "captures": hashes}, indent=2) + "\n")
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
