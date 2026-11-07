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
check(C.extract_raw(built, "STORE") == C.extract_raw(source, "STORE"), "STORE bytes match the snapshot")
check(C.extract_raw(built, "EXTRA") == C.extract_raw(source, "EXTRA"), "EXTRA bytes match the snapshot")
check('const FS_TOKEN=""' in built and "formsubmit.co" not in built and "api.github.com" not in built, "token empty and default hosts blocked")
check("current data nonpublishable preview" in built, "preview is labeled nonpublishable current data")

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
