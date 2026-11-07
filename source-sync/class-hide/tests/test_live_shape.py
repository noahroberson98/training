"""Live-shape synthetic cases. No live files, no network, no installed symlink."""
import json, os, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "runtime"))
import build
import merge

ok = True

def check(c, m):
    global ok
    print(("PASS " if c else "FAIL ") + m)
    ok = ok and bool(c)

KEY = "2099-06-01|10:00|APEX"
OTHER = "2099-06-03|09:00|THIS STRENGTH"
NOW = datetime(2099, 6, 4, 12, 0, 0)
OV = {
    KEY: {
        "session_key": KEY, "status": "cancelled", "attendance": "skipped", "hidden": True,
        "provider_cancellation_verified": False, "source": "Synthetic User",
        "reported_at": "2099-06-03T11:45:00-06:00",
    }
}

def row(date, time, name, status, source="synthetic feed"):
    return {"date": date, "time": time, "class": name, "type": "class", "coach": "", "status": status, "source": source}

def run_hist(feed, hist, overrides):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "class_history.json")
        Path(path).write_text(json.dumps(hist))
        rows = build.update_class_history(feed, hist_path=path, now=NOW, overrides=overrides)
        return {f"{r['date']}|{r['time']}|{r['class']}": r for r in rows}

base = {
    KEY: {"date": "2099-06-01", "time": "10:00", "class": "APEX", "type": "class", "coach": "",
          "status": "RESERVED", "csv_status": "RESERVED", "source": "synthetic feed"},
    OTHER: {"date": "2099-06-03", "time": "09:00", "class": "THIS STRENGTH", "type": "class", "coach": "",
            "status": "RESERVED", "csv_status": "RESERVED", "source": "synthetic feed"},
}
mutated = [row("2099-06-01", "10:00", "APEX", "CANCELLED"), row("2099-06-03", "09:00", "THIS STRENGTH", "RESERVED")]
got = run_hist(mutated, base, OV)
apex, other = got[KEY], got[OTHER]
check(apex.get("csv_status") == "RESERVED" and apex.get("provider_status") == "RESERVED", "user-mutated CANCELLED feed keeps the established provider baseline")
check(apex.get("feed_status") == "CANCELLED", "raw feed column is recorded separately")
check(apex.get("status") == "CANCELLED" and apex.get("cancel_source") == "user", "display status is the user report")
check(apex.get("provider_cancellation_verified") is False and apex.get("cancel_source") != "confirmed", "user report is not provider confirmation")
check(other.get("csv_status") == "RESERVED" and other.get("status") == "RESERVED" and not other.get("hidden"), "the other booking provider status stays reserved")

plain = run_hist(mutated, base, None)
pg = plain[KEY]
check(pg.get("csv_status") == "CANCELLED" and pg.get("provider_cancellation_verified") is not True, "a feed change without a user report updates the baseline and does not verify the provider")
check(pg.get("cancel_source") not in ("user", "confirmed"), "that feed change is not labeled user or confirmed")

missing_base = run_hist([row("2099-06-01", "10:00", "APEX", "CANCELLED")], {}, OV)
mb = missing_base[KEY]
check(mb.get("csv_status") == "unknown" and mb.get("provider_status") == "unknown", "no established baseline stays unknown instead of a hardcoded reserved or a copied cancel")
check(mb.get("provider_cancellation_verified") is False and mb.get("cancel_source") == "user", "missing baseline is still an unverified user report")

established_cancel = {
    KEY: {"date": "2099-06-01", "time": "10:00", "class": "APEX", "type": "class", "coach": "",
          "status": "CANCELLED", "csv_status": "CANCELLED", "provider_status": "CANCELLED", "source": "synthetic feed"},
}
kept = run_hist([row("2099-06-01", "10:00", "APEX", "CANCELLED")], established_cancel, OV)[KEY]
check(kept.get("csv_status") == "CANCELLED" and kept.get("provider_status") == "CANCELLED", "an established provider cancel is not rewritten to reserved")
check(kept.get("provider_cancellation_verified") is False, "an established cancel string is still not provider verification")

store = {"schema": 1, "workouts": {
    "2099-06-01|APEX": {"date": "2099-06-01", "title": "APEX", "type": "class", "status": "completed", "status_note": None,
        "session_key": KEY, "exercises": [{"label": "A1", "name": "Row", "sets": 3, "reps": 8, "warmup": False,
            "actuals": {"sets": [{"weight_lb": 40, "reps": 8}]}}]},
    "2099-06-03|Strength": {"date": "2099-06-03", "title": "Strength", "type": "Strength", "status": "completed", "status_note": None,
        "status_locked": True, "session_key": OTHER, "exercises": [{"label": "B1", "name": "Squat", "sets": 1, "reps": 5,
            "actuals": {"sets": [{"weight_lb": 185, "reps": 5}]}}]},
    "2099-06-06|Upper Body": {"date": "2099-06-06", "title": "Upper Body", "type": "Strength", "status": "completed", "status_note": None,
        "exercises": [{"label": "A1", "name": "Bench Press", "sets": 3, "reps": 8, "actuals": {"sets": [
            {"weight_lb": 135, "reps": 8}, {"weight_lb": 135, "reps": 8}, {"weight_lb": 145, "reps": 6}]}}]},
}}
batch = {"workouts": [
    {"date": "2099-06-01", "title": "APEX", "status": "completed", "exercises": [{"label": "A1", "name": "Row", "sets": 3, "reps": 8}]},
    {"date": "2099-06-03", "title": "Strength", "status": "planned", "exercises": [{"label": "B1", "name": "Squat", "sets": 1, "reps": 5}]},
    {"date": "2099-06-06", "title": "Upper Body", "status": "completed", "exercises": [{"label": "A1", "name": "Bench Press", "sets": 3, "reps": 8}]},
]}
merge.merge(store, batch, "synthetic-live-shape", overrides=OV)
bench = [s for s in store["workouts"]["2099-06-06|Upper Body"]["exercises"][0]["actuals"]["sets"]]
check(store["workouts"]["2099-06-01|APEX"]["exercises"][0]["actuals"]["sets"] == [{"weight_lb": 40, "reps": 8}], "row set stays one 40x8")
check(store["workouts"]["2099-06-03|Strength"]["status"] == "completed" and store["workouts"]["2099-06-03|Strength"]["status_locked"] is True, "locked strength stays completed")
check(bench == [{"weight_lb": 135, "reps": 8}, {"weight_lb": 135, "reps": 8}, {"weight_lb": 145, "reps": 6}], "duplicate bench rows stay two occurrences")

runtime = HERE / "runtime"
with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    td, fd = root / "training-dashboard", root / "fitness-dashboard"
    (td / "scripts").mkdir(parents=True)
    (td / "data").mkdir()
    fd.mkdir()
    for name in ("build.py", "merge.py", "common.py", "whoop_pair.py", "template.html"):
        shutil.copyfile(runtime / name, td / "scripts" / name)
    canon = fd / "user_overrides.json"
    canon.write_text(json.dumps({"schema": 1, "sessions": OV}) + "\n")
    os.symlink(canon, td / "data" / "user_overrides.json")
    (td / "data" / "class_history.json").write_text(json.dumps(base))
    (td / "data" / "workouts.json").write_text(json.dumps({"schema": 1, "workouts": store["workouts"]}))
    whoop = td / "whoop"
    whoop.mkdir()
    (whoop / "whoop_daily.csv").write_text("date,recovery_pct\n")
    (whoop / "whoop_sessions.csv").write_text("date,session,notes\n")
    feed = td / "feed.csv"
    feed.write_text("date,time,class,type,coach,status,source\n2099-06-01,10:00,APEX,class,,CANCELLED,synthetic feed\n2099-06-03,09:00,THIS STRENGTH,class,,RESERVED,synthetic feed\n")
    batch_path = td / "batch.json"
    batch_path.write_text(json.dumps(batch))
    env = os.environ.copy()
    m = subprocess.run([sys.executable, "scripts/merge.py", str(batch_path), "--store", str(td / "data" / "workouts.json")], cwd=td, capture_output=True, text=True)
    b = subprocess.run([sys.executable, "scripts/build.py", "--store", str(td / "data" / "workouts.json"), "--out", str(td / "out.html"), "--csv", str(td / "out.csv"), "--classes", str(feed), "--whoop", str(whoop / "whoop_daily.csv")], cwd=td, capture_output=True, text=True)
    check(m.returncode == 0 and b.returncode == 0, "staged generators exit 0 through the synthetic symlink")
    resolved = Path(os.path.realpath(td / "data" / "user_overrides.json"))
    check(resolved == canon.resolve() and not Path("/workspace/training-dashboard/data/user_overrides.json").exists(), "symlink resolves only inside this temp tree")
    hist = json.loads((td / "data" / "class_history.json").read_text())
    built = hist[KEY]
    check(built.get("csv_status") == "RESERVED" and built.get("feed_status") == "CANCELLED" and built.get("provider_cancellation_verified") is False, "build.py keeps the provider baseline when the linked override is unverified")
    html = (td / "out.html").read_text()
    sentence = "You reported this cancelled. The provider has not confirmed it. The gym list still says reserved."
    check("You reported this cancelled. The provider has not confirmed it." in html and "The gym list still says reserved." in html, "built page states the user report and the unverified gym list")
    check("provider_cancellation_verified\": false" in html or "provider_cancellation_verified\":false" in html, "built page keeps provider verification false")
    out_copy = HERE / "assembled" / "live-shape.html"
    out_copy.write_text(html)
    shots = HERE / "shots"
    shots.mkdir(exist_ok=True)
    import threading
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(td)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    from playwright.sync_api import sync_playwright
    blocked = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        ctx.add_init_script("""(() => { const o = Storage.prototype.setItem; Storage.prototype.setItem = function(k,v){ if (window.__failStorage && k === "tpDash.classHide.v1") throw new DOMException("quota","QuotaExceededError"); return o.call(this,k,v); }; })();""")
        def route(r):
            if r.request.url.startswith("http://127.0.0.1"):
                r.continue_()
            else:
                blocked.append(r.request.url); r.abort()
        ctx.route("**/*", route)
        page = ctx.new_page()
        page.goto(f"http://127.0.0.1:{port}/out.html?tab=workout&day=2099-06-01", wait_until="domcontentloaded")
        page.wait_for_selector("#hidden")
        card = page.locator(f"#hidden [data-key='{KEY}']")
        note = card.locator(".clsnote").inner_text()
        badge = card.locator(".bdg").inner_text()
        geom = card.locator(".cname").evaluate("""el => ({text: el.textContent, clipped: el.scrollWidth > el.clientWidth + 1, w: el.getBoundingClientRect().width, whiteSpace: getComputedStyle(el).whiteSpace})""")
        note_geom = card.locator(".clsnote").evaluate("""el => ({clipped: el.scrollWidth > el.clientWidth + 1, whiteSpace: getComputedStyle(el).whiteSpace})""")
        check(note == sentence and badge == "Reserved" and card.get_attribute("data-provider") == "false" and card.get_attribute("data-csv") == "RESERVED", "hidden card separates the user report from the gym list")
        check(geom["text"] == "APEX" and not geom["clipped"] and geom["w"] > 140 and not note_geom["clipped"] and page.evaluate("() => window.innerWidth") == 390, "live-shape name and explanation are readable at 390px")
        check("Hide and Undo change visibility only in this browser." in page.locator("#hideScope").inner_text(), "scope still says a local choice wins over the built choice")
        page.screenshot(path=str(shots / "live-shape-hidden.png"), full_page=True)
        undo = card.locator("[data-undocls]")
        hit = undo.evaluate("""el => { const r = el.getBoundingClientRect(); const top = document.elementFromPoint(r.x+r.width/2, r.y+r.height/2); return {reached: !!(top && (top===el || el.contains(top)))}; }""")
        undo.click(force=False)
        shown = page.locator(f"#booked [data-key='{KEY}']")
        check(hit["reached"] and shown.count() == 1 and sentence in shown.inner_text() and shown.get_attribute("data-provider") == "false" and shown.get_attribute("data-hide-store") == "phone", "undo shows the row locally and leaves provider verification false")
        page.screenshot(path=str(shots / "live-shape-undo.png"), full_page=True)
        page.evaluate("() => { window.__failStorage = true; }")
        hide = shown.locator("[data-hidecls]")
        hide.click(force=False)
        warn = page.locator("#classHideWarn").inner_text() if page.locator("#classHideWarn").count() else ""
        check(warn == "Not saved on this phone. Visibility has not changed." and shown.count() == 1, "failed hide leaves the live-shape row visible")
        page.screenshot(path=str(shots / "live-shape-save-failed.png"), full_page=True)
        check(blocked == [], "live-shape browser stays on the local file")
        browser.close()
    httpd.shutdown()

print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
