"""History estimated-1RM progression. Formulas, provenance, and the example page.

No live store, no outbound send. Node checks the template functions. Playwright
checks the sanitized example page only.
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import preview_history as P

ok = True
def check(c, m):
    global ok
    print(("PASS " if c else "FAIL ") + m)
    ok = ok and bool(c)

def epley(w, r):
    return w * (1 + r / 30.0)

def brzycki(w, r):
    return w * 36.0 / (37.0 - r)

TPL = (ROOT / "scripts" / "template.html").read_text()
a = TPL.find("/*E1RM_PURE_BEGIN*/")
b = TPL.find("/*E1RM_PURE_END*/")
check(a > 0 and b > a, "template has the estimate block")
pure = TPL[a:b + len("/*E1RM_PURE_END*/")]
check('const FS_TOKEN="REDACTED_FORMSUBMIT_ALIAS"' in TPL, "generator token line was not rewritten")
check("https://formsubmit.co/ajax/" in TPL and "https://api.github.com" in TPL, "generator send hosts stay in source")
check("function keepRecordedClock(" in TPL, "recorded-clock repair still in the template")
check("<canvas" not in TPL.lower(), "chart is not a canvas element")
check(abs(epley(100, 10) - brzycki(100, 10)) < 1e-9, "Epley and Brzycki meet at 10 reps")
check(abs(brzycki(200, 1) - 200) < 1e-9, "Brzycki at 1 rep is the load")
check(abs(epley(200, 1) - 200 * 31 / 30) < 1e-9, "Epley at 1 rep would inflate, so the chart must not use it")

cases = [
    ("ten", {"weight_lb": 100, "reps": 10}, {"name": "Bench"}, dict(ok=True, method="epley", primary=epley(100, 10), brzycki=brzycki(100, 10), confidence="estimate", unit="lb", basis="stored_lb")),
    ("six", {"weight_lb": 100, "reps": 6}, {"name": "Bench"}, dict(ok=True, primary=120.0, brzycki=brzycki(100, 6), confidence="estimate")),
    ("single", {"weight_lb": 200, "reps": 1}, {"name": "Bench"}, dict(ok=True, method="actual_single", primary=200.0, brzycki=None, confidence="actual_single")),
    ("eleven", {"weight_lb": 90, "reps": 11}, {"name": "Bench"}, dict(ok=True, method="epley", primary=epley(90, 11), brzycki=None, confidence="estimate")),
    ("twelve", {"weight_lb": 90, "reps": 12}, {"name": "Bench"}, dict(ok=True, primary=epley(90, 12), brzycki=None, confidence="estimate")),
    ("thirteen", {"weight_lb": 40, "reps": 13}, {"name": "Bench"}, dict(ok=True, primary=epley(40, 13), brzycki=None, confidence="low")),
    ("thirtyseven", {"weight_lb": 40, "reps": 37}, {"name": "Bench"}, dict(ok=True, primary=epley(40, 37), brzycki=None, confidence="low")),
    ("zero", {"weight_lb": 0, "reps": 8}, {"name": "Bench"}, dict(ok=False, reason="invalid")),
    ("missingw", {"reps": 8}, {"name": "Bench"}, dict(ok=False, reason="invalid")),
    ("missingr", {"weight_lb": 50}, {"name": "Bench"}, dict(ok=False, reason="invalid")),
    ("frac", {"weight_lb": 100, "reps": 8.5}, {"name": "Bench"}, dict(ok=False, reason="invalid")),
    ("nan", {"weight_lb": None, "reps": 8}, {"name": "Bench"}, dict(ok=False, reason="invalid")),
    ("plan", {"weight_lb": 100, "reps": 8, "per_plan": True}, {"name": "Bench"}, dict(ok=False, reason="plan_filled")),
    ("round", {"weight_lb": 80, "reps": 8, "round": True}, {"name": "Bench"}, dict(ok=False, reason="plan_filled")),
    ("warmex", {"weight_lb": 45, "reps": 10}, {"name": "Bench", "warmup": True}, dict(ok=False, reason="warmup")),
    ("warmset", {"weight_lb": 45, "reps": 10, "warmup": True}, {"name": "Bench"}, dict(ok=False, reason="warmup")),
    ("assist", {"weight_lb": 50, "reps": 8}, {"name": "Example Assisted Pull-Up"}, dict(ok=False, reason="assistance")),
    ("kg", {"weight_kg": 40, "reps": 5}, {"name": "Example KG Row"}, dict(ok=True, unit="kg", basis="kg", primary=epley(40, 5), method="epley")),
    ("conflict", {"weight_lb": 100, "weight_kg": 10, "reps": 5}, {"name": "Press"}, dict(ok=False, reason="unit_conflict")),
    ("agree", {"weight_lb": 88, "weight_kg": 40, "reps": 5}, {"name": "Press"}, dict(ok=True, unit="lb", primary=epley(88, 5))),
    ("db", {"weight_lb": 25, "reps": 8}, {"name": "Example DB Curl"}, dict(ok=True, basis="per_hand_unconfirmed", primary=epley(25, 8), unit="lb")),
]

node_src = pure + """
const cases = %s;
const out = cases.map(c => e1rmEstimate(c.set, c.exercise));
const dedup = e1rmSession([
  {id:"a", weight_lb:100, reps:5},
  {id:"a", weight_lb:140, reps:5},
  {id:"b", weight_lb:100, reps:5},
  {weight_lb:100, reps:8},
  {weight_lb:100, reps:8}
], {name:"Bench"});
const prefer = e1rmSession([
  {weight_lb:105, reps:1},
  {weight_lb:40, reps:15},
  {weight_lb:200, reps:10, per_plan:true}
], {name:"Bench"});
const onlyLow = e1rmSession([{weight_lb:40, reps:20}], {name:"Bench"});
const series = e1rmSeries([
  {key:"d1", date:"2026-10-01", title:"A", sets:[{weight_lb:100, reps:8}], exercise:{name:"Bench"}},
  {key:"d2", date:"2026-10-08", title:"A", sets:[{weight_lb:100, reps:5}], exercise:{name:"Bench"}},
  {key:"kg", date:"2026-10-16", title:"A", sets:[{weight_kg:40, reps:5}], exercise:{name:"Bench"}}
]);
const fmt = [126.6666666667, 116.6666666667, 121, 66.6666666667, 129.8333333333, 124.1379310345].map(e1rmFmt);
const incline = e1rmEstimate({weight_lb:25, reps:8}, {name:"High Incline Press"});
const assumed = e1rmSeries([{key:"2026-11-06|Upper Body", date:"2026-11-06", title:"Upper Body", assumed:true, sets:[{weight_lb:100, reps:8}], exercise:{name:"Machine Row"}}]);
console.log(JSON.stringify({out, dedup, prefer, onlyLow, series, fmt, incline, assumed}));
""" % json.dumps([{"set": s, "exercise": e} for _, s, e, _ in cases])
node_path = Path(tempfile.mkdtemp()) / "e1rm-cases.js"
# NaN cannot be JSON. Patch the missing-weight null case; add a NaN case in the script.
node_src = node_src.replace(
    'console.log(JSON.stringify({out, dedup, prefer, onlyLow, series, fmt, incline, assumed}));',
    'out.push(e1rmEstimate({weight_lb: NaN, reps: 8}, {name:"Bench"}));\n'
    'out.push(e1rmEstimate({weight_lb: Infinity, reps: 8}, {name:"Bench"}));\n'
    'console.log(JSON.stringify({out, dedup, prefer, onlyLow, series, fmt, incline, assumed}));'
)
node_path.write_text(node_src)
proc = subprocess.run(["node", str(node_path)], capture_output=True, text=True)
check(proc.returncode == 0, "node ran the estimate block: " + (proc.stderr[-300:] if proc.returncode else "ok"))
got = json.loads(proc.stdout) if proc.returncode == 0 else None
if got:
    for i, (name, _s, _e, exp) in enumerate(cases):
        row = got["out"][i]
        good = True
        for k, v in exp.items():
            if v is None:
                good = good and row.get(k) is None
            elif isinstance(v, float):
                good = good and row.get(k) is not None and abs(row[k] - v) < 1e-6
            else:
                good = good and row.get(k) == v
        check(good, "estimate " + name + " " + json.dumps(row))
    check(got["out"][len(cases)]["reason"] == "invalid" and got["out"][len(cases) + 1]["reason"] == "invalid", "NaN and Infinity are not a load")
    d = got["dedup"]["points"][0]
    check(d["eligible"] == 4 and d["topWeight"] == 100 and abs(d["primary"] - epley(100, 8)) < 1e-6, "same id dropped, repeated 100x8 kept, best is the 8: %s" % d)
    p = got["prefer"]["points"][0]
    check(p["method"] == "actual_single" and p["primary"] == 105 and p["topWeight"] == 105 and p["confidence"] == "actual_single", "single beats a heavier plan fill and a high-rep set: %s" % p)
    low = got["onlyLow"]["points"][0]
    check(low["confidence"] == "low" and low["brzycki"] is None and abs(low["primary"] - epley(40, 20)) < 1e-6, "only a 20-rep set stays low confidence: %s" % low)
    ser = got["series"]
    check([x["date"] for x in ser["chart"]] == ["2026-10-01", "2026-10-08"], "same-unit sessions stay in date order")
    check(len(ser["held"]) == 1 and ser["held"][0]["unit"] == "kg", "a kilogram session is not plotted on the pound line")
    check(got["fmt"] == ["126.7", "116.7", "121", "66.7", "129.8", "124.1"], "display rounding " + str(got["fmt"]))
    inc = got["incline"]
    check(inc["ok"] and inc["basis"] == "stored_lb" and abs(inc["primary"] - epley(25, 8)) < 1e-6 and abs(inc["primary"] - epley(50, 8)) > 1, "incline load is not doubled")
    ap = got["assumed"]["points"][0]
    check(ap["assumed"] is True and ap["basis"] == "stored_lb" and abs(ap["primary"] - epley(100, 8)) < 1e-6, "assumed pounds stay on the pound series at the stored weight")

# UI on the example page only
tmp = tempfile.mkdtemp()
html = P.write_preview(tmp)
check("Example data" in html and "blocked-outbound" in html and "formsubmit.co" not in html, "preview is marked and blocked")
check("Not a real training log" in html or "example" in html.lower(), "preview is labeled an example")

from playwright.sync_api import sync_playwright
CHROME = "/usr/bin/google-chrome"
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    hits = {"n": 0}
    def route_all(route):
        url = route.request.url
        if url.startswith("http://") or url.startswith("https://"):
            hits["n"] += 1
            route.abort()
        else:
            route.continue_()
    ctx.route("**/*", route_all)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    seed = json.dumps({"example|clock": {"started_at": "2026-10-01T15:00:00.000Z", "ended_at": "2026-10-01T15:30:00.000Z", "exercises": {}}})
    page.add_init_script("localStorage.setItem('tpDash.logs.v2', %s);" % json.dumps(seed))
    page.goto("file://" + os.path.join(tmp, "synthetic-history.html") + "?tab=history&ex=example-bench-press")
    page.wait_for_selector("#e1rm-panel")
    before = page.evaluate("localStorage.getItem('tpDash.logs.v2')")
    check(page.locator(".exbanner").inner_text().find("Example") >= 0, "example banner is visible")
    check(page.get_attribute("#e1rm-panel", "data-e1rm-state") == "chart", "bench opens on the chart")
    check("Epley" in page.inner_text("#e1rm-panel") and "Brzycki" in page.inner_text("#e1rm-panel"), "both formulas are named")
    check("not a suggestion to attempt" in page.inner_text("#e1rm-panel").lower() or "not a suggestion to attempt one" in page.inner_text("#e1rm-panel"), "estimate is not a max attempt")
    rows = page.eval_on_selector_all("#e1rm-panel tbody tr", "els => els.map(e => ({date:e.dataset.date, method:e.dataset.method, conf:e.dataset.confidence, top:+e.dataset.top, reps:+e.dataset.topReps, primary:+e.dataset.primary, brz:e.dataset.brzycki, unit:e.dataset.unit}))")
    check([r["date"] for r in rows] == ["2026-10-01", "2026-10-08", "2026-10-15", "2026-10-15", "2026-10-22", "2026-10-29"], "bench sessions stay in date order, same day kept apart: %s" % [r["date"] for r in rows])
    check(abs(rows[0]["primary"] - epley(100, 8)) < 1e-6 and rows[0]["top"] == 100 and rows[0]["reps"] == 8, "Oct 1 top set 100x8 and Epley")
    check(rows[0]["brz"] not in ("", None) and abs(float(rows[0]["brz"]) - brzycki(100, 8)) < 1e-6, "Oct 1 Brzycki is the comparison, not the primary")
    check(rows[2]["method"] == "actual_single" and rows[2]["primary"] == 105 and rows[2]["top"] == 105, "Oct 15 single is 105, not the 200 plan fill or the 15-rep set")
    check(abs(rows[3]["primary"] - 121) < 1e-6 and rows[3]["method"] == "epley", "later same-day session stays its own point")
    check(rows[4]["conf"] == "estimate" and rows[4]["brz"] == "" and abs(rows[4]["primary"] - epley(95, 11)) < 1e-6, "11 reps keep Epley and omit Brzycki")
    check(rows[5]["conf"] == "low" and abs(rows[5]["primary"] - epley(40, 20)) < 1e-6, "20 reps are low confidence")
    text = page.inner_text("#e1rm-panel")
    check("126.7" in text and "Low confidence" in text and "Since Oct 22" in text, "latest and change use real session values")
    check("Example note. Not a real log." in text, "session note is kept as text")
    aside = page.locator("#aside").inner_text()
    check("Best Estimates" in aside and "200×10" not in aside and "50×8" not in aside, "aside uses estimates and skips plan-filled and assisted loads")
    check(rows[2]["brz"] == "", "a logged single does not get a Brzycki comparison")
    panel = page.inner_text("#e1rm-panel")
    check("Brzycki is only shown for 2–10 reps." in panel, "Brzycki policy is 2–10 reps")
    check("Failure/effort status is not consistently recorded or independently verified." in panel, "effort caveat does not claim the log is silent")
    check("does not say a set was to failure" not in panel, "old failure caveat is gone")
    check("2026" in panel and "Logged Only" in page.inner_text("body"), "year context and Title Case filter")
    style = page.evaluate("""()=>{const th=document.querySelector('.e1rm-table th.num'); const td=document.querySelector('.e1rm-table td.num'); return {tf:th&&getComputedStyle(th).textTransform, al:td&&getComputedStyle(td).textAlign};}""")
    check(style["tf"] == "none" and style["al"] == "right", "numeric headers are not forced uppercase and numbers align right: %s" % style)
    tips = page.eval_on_selector_all("#e1rm-panel svg title", "els => els.map(e => e.textContent)")
    check(tips and all(("Epley" in t or "Logged single" in t) and "2026" in t and "×" in t for t in tips), "every point has an exact tooltip")
    check("45×10" not in text and "200×10" not in text, "warm-up and plan-filled loads are not charted as the top set")
    check(page.locator("[data-wend]").count() == 0, "History does not show End Workout")
    page.select_option("#ex-pick", "example-empty-press")
    page.wait_for_selector("[data-e1rm-state=empty]")
    check(page.locator("#e1rm-panel svg").count() == 0, "no chart when nothing is eligible")
    check("No estimated max" in page.inner_text("#e1rm-panel"), "empty state is explicit")
    check("plan-filled" in page.inner_text("#e1rm-panel"), "empty state says plan-filled sets were left out")
    page.select_option("#ex-pick", "example-db-curl")
    page.wait_for_selector("[data-e1rm-state=chart]")
    db = page.eval_on_selector_all("#e1rm-panel tbody tr", "els => els.map(e => +e.dataset.primary)")
    check(abs(db[-1] - epley(25, 8)) < 1e-6 and abs(db[-1] - epley(50, 8)) > 1, "dumbbell load is not doubled")
    check("not doubled" in page.inner_text("#e1rm-panel"), "per-hand basis is labeled")
    page.select_option("#ex-pick", "example-assisted-pull-up")
    check(page.get_attribute("#e1rm-panel", "data-e1rm-state") == "empty", "assisted load is not an estimated max")
    page.select_option("#ex-pick", "example-kg-row")
    kg = page.inner_text("#e1rm-panel")
    check("kg" in kg and "46.7" in kg and "Not converted" in kg, "kilograms stay kilograms")
    page.select_option("#ex-pick", "example-mixed-row")
    mixed = page.inner_text("#e1rm-panel")
    check("another unit" in mixed and "No earlier session" in mixed, "mixed units are not compared as one trend")
    cap = page.locator("#e1rm-panel caption").inner_text()
    check("not on the chart" in cap and "The same numbers are in the chart" not in cap, "mixed-unit caption does not claim every table row is charted")
    page.select_option("#ex-pick", "example-img-alt-x-quote-press")
    page.wait_for_selector("[data-e1rm-state=chart]")
    svg = page.inner_html("#e1rm-panel svg")
    check(page.locator("#e1rm-panel svg img").count() == 0 and "&lt;img" in svg and "&amp;" in svg, "tooltip markup escapes the canary once")
    tip_text = page.eval_on_selector("#e1rm-panel svg title", "e => e.textContent")
    check("<img" in tip_text and "&" in tip_text and '"' in tip_text, "tooltip text keeps the canary characters")
    page.select_option("#ex-pick", "example-conflict-press")
    check(page.get_attribute("#e1rm-panel", "data-e1rm-state") == "empty", "conflicting units produce no estimate")
    page.select_option("#ex-pick", "example-push-up")
    check(page.get_attribute("#e1rm-panel", "data-e1rm-state") == "empty", "reps without a load are not a bodyweight max")
    after = page.evaluate("localStorage.getItem('tpDash.logs.v2')")
    check(after == before == seed, "selecting exercises did not write the log or the clock")
    page.click("#tabs button[data-tab=week]")
    page.click("#tabs button[data-tab=history]")
    page.wait_for_selector("#e1rm-panel")
    check(page.evaluate("localStorage.getItem('tpDash.logs.v2')") == seed, "opening History did not write storage")
    check(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), "history does not widen the 390px page")
    check(hits["n"] == 0, "example page made no outbound request")
    check(not errs, "no page errors " + "; ".join(errs))
    browser.close()

print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
