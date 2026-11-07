"""History on the sanitized current snapshot. STORE/EXTRA stay byte-identical.

Requires the snapshot path as argv 1. Fresh browser context. HTTP(S) is aborted.
"""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import preview_current as C

if len(sys.argv) < 2:
    print("FAIL snapshot path required")
    sys.exit(2)
source = Path(sys.argv[1]).read_text(encoding="utf-8")
ok = True
def check(c, m):
    global ok
    print(("PASS " if c else "FAIL ") + m)
    ok = ok and bool(c)

import tempfile
tmp = tempfile.mkdtemp()
html = C.write_preview(tmp, str(ROOT / "scripts" / "template.html"), sys.argv[1])
built = Path(tmp, "current-history.html").read_text(encoding="utf-8")
store_raw = C.extract_raw(built, "STORE")
check(store_raw == C.extract_raw(source, "STORE"), "STORE bytes match the snapshot")
check(C.extract_raw(built, "EXTRA") == C.extract_raw(source, "EXTRA"), "EXTRA bytes match the snapshot")
check(all(("t240u#%d" % i) in store_raw for i in range(6)), "all six chat set ids remain in STORE")
check("/*RELAY*/" not in built and "training-requests/issues" not in built, "dormant cancellation relay is stripped, matching the run12 page")
check("current-data-preview" not in built, "debug build slug is absent")
check("Nov 6, 2026 6:27 PM CT" in built and "historical preview, not for publication" in built, "menu uses the snapshot's own build clock")
check('const FS_TOKEN=""' in built and "formsubmit.co" not in built and "api.github.com" not in built, "token empty and default hosts blocked")
check("historical preview, not for publication" in built, "preview is labeled a historical preview")

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
    page.goto("file://" + os.path.join(tmp, "current-history.html") + "?tab=history&ex=machine-row")
    page.wait_for_selector("#e1rm-panel")
    before = page.evaluate("localStorage.getItem('tpDash.logs.v2')")
    check(page.evaluate("FS_TOKEN") == "", "page token is empty")
    check(page.evaluate("typeof knownLoadSet==='function' && typeof weekVolumeText==='function' && typeof unitAssumptionNote==='function'"), "run12 known-load helpers are present")
    text = page.inner_text("#e1rm-panel")
    check("Pounds assumed" in text and "not converted or doubled" in text, "Machine Row shows assumed pounds and does not double")
    check("Failure/effort status is not consistently recorded or independently verified." in text, "effort caveat matches the recorded notes")
    check("does not say a set was to failure" not in text, "effort caveat does not deny the Oct 30 note")
    latest = page.locator("[data-e1rm-latest]").inner_text()
    check("fail" not in latest.lower(), "the latest session is not labeled as a failure")
    check("2026" in text and "Nov 6, 2026" in text, "table dates include the source year")
    check("Best Estimates" in page.locator("#aside").inner_text() and "Logged Only" in page.inner_text("body"), "Title Case labels")
    style = page.evaluate("""()=>{const th=document.querySelector('.e1rm-table th.num'); const td=document.querySelector('.e1rm-table td.num'); return {tf:th&&getComputedStyle(th).textTransform, al:td&&getComputedStyle(td).textAlign};}""")
    check(style["tf"] == "none" and style["al"] == "right", "table headers are not forced uppercase and numbers align right")
    tips = page.eval_on_selector_all("#e1rm-panel svg title", "els => els.map(e => e.textContent)")
    check(len(tips) == 2 and all("2026" in t and "×" in t and "Epley" in t and ("estimate" in t or "low confidence" in t) for t in tips), "Machine Row points have exact tooltips")
    page.locator("#e1rm-panel .e1rm-pt").first.dispatch_event("mouseover")
    page.wait_for_timeout(100)
    shown = page.locator("#e1rm-tip").inner_text()
    check(shown == tips[0], "visible tooltip matches the SVG title: %r vs %r" % (shown, tips[0]))
    check("Epley" in text and "not a suggestion to attempt one" in text, "estimate is labeled and is not a max attempt")
    rows = page.eval_on_selector_all("#e1rm-panel tbody tr", "els => els.map(e => e.dataset.date)")
    check(rows == ["2026-10-30", "2026-11-06"], "Machine Row progression is the two logged dates: %s" % rows)
    six = page.evaluate("""()=>{
      const w=W.find(x=>x.key==='2026-11-06|Upper Body');
      let n=0;
      ['Machine Row','High Incline Press'].forEach(name=>{
        const e=w.exercises.find(x=>x.name===name);
        n += allSets(w,e).filter(s=>knownLoadSet(s)&&!s.per_plan&&!s.round).length;
      });
      return n;
    }""")
    check(six == 6, "Nov 6 keeps six logged actual sets on Machine Row and High Incline Press")
    incline = page.evaluate("""()=>{
      const s=sessions().find(x=>x.name==='High Incline Press');
      const series=e1rmSeries(e1rmItems(s));
      return series.chart.map(p=>({ok:Math.abs(p.primary-p.bestWeight*(1+p.bestReps/30))<1e-6, doubled:Math.abs(p.primary-(p.bestWeight*2)*(1+p.bestReps/30))<1e-6}));
    }""")
    check(incline and all(p["ok"] and not p["doubled"] for p in incline), "High Incline Press estimate uses the stored weight once")
    clock = page.evaluate("""()=>{const w=W.find(x=>x.key==='2026-11-06|Upper Body'); return {s:w.started_at, e:w.ended_at, local:local[w.key]||null};}""")
    page.select_option("#ex-pick", "abmat-sit-up")
    page.wait_for_selector("[data-e1rm-state=empty]")
    check("No estimated max" in page.inner_text("#e1rm-panel"), "AbMat has no estimated max")
    check(page.locator("[data-wend]").count() == 0, "History does not show End Workout")
    after = page.evaluate("localStorage.getItem('tpDash.logs.v2')")
    clock2 = page.evaluate("""()=>{const w=W.find(x=>x.key==='2026-11-06|Upper Body'); return {s:w.started_at, e:w.ended_at, local:local[w.key]||null};}""")
    check(before is None and after is None and clock == clock2, "opening History and changing exercise did not write a log or the clock")
    check(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), "390px history does not scroll sideways")
    check(hits["n"] == 0, "no outbound HTTP request")
    check(not errs, "no page errors " + "; ".join(errs))
    browser.close()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
