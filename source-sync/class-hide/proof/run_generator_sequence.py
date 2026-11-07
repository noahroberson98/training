"""Proof-only mobile sequence. Does not edit the Style-passed template or generators.

Copies the committed build.py, merge.py, common.py, whoop_pair.py, and template.html
and runs those copies. Synthetic feeds and stores are written only under proof/work.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
REPO = SRC.parents[1]
RUNTIME = SRC / "runtime"
OUT = HERE / "out"
WORK = HERE / "work"
HEAD = "c0d9143227040f682e070fe4746f95f395cf0e25"
PASSED_HTML = "d6e51ce0310e6c9fe29825e584e0554149e54ada9c861ea37f9f5442e86f252a"
APEX = "2099-01-01|10:00|APEX"
SETS = {
    "2099-01-01|APEX": [("A1", "Row", [(40, 8)])],
    "2099-01-03|Strength": [("B1", "Squat", [(185, 5)])],
    "2099-01-06|Upper Body": [("A1", "Bench Press", [(135, 8), (135, 8), (145, 6)])],
}

log = []
shots = []


def sha(path):
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def now():
    return datetime.now(timezone.utc).isoformat()


def record(step, **fields):
    row = {"at": now(), "step": step, **fields}
    log.append(row)
    print(step, json.dumps({k: v for k, v in fields.items() if k in ("ok", "exit", "page_sha", "feed_sha", "storage", "note")}, default=str)[:500])
    return row


def run_cmd(cmd, cwd, label):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    dest = OUT / "commands" / f"{label}.log"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        "$ " + " ".join(cmd) + f"\nexit {proc.returncode}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}\n"
    )
    record(label, command=cmd, cwd=str(cwd), exit=proc.returncode, stdout=proc.stdout, stderr=proc.stderr, log=str(dest))
    if proc.returncode != 0:
        raise SystemExit(f"{label} exited {proc.returncode}")
    return proc


def copy_runtime(root):
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (root / "data").mkdir()
    for name in ("build.py", "merge.py", "common.py", "whoop_pair.py", "template.html"):
        shutil.copyfile(RUNTIME / name, scripts / name)
    pins = {}
    for name in ("build.py", "merge.py", "common.py", "whoop_pair.py", "template.html"):
        digest, size = sha(scripts / name)
        origin, _ = sha(RUNTIME / name)
        pins[name] = {"sha256": digest, "bytes": size, "matches_committed": digest == origin}
        if digest != origin:
            raise SystemExit(f"copy drift {name}")
    return pins


def write_inputs(root, overrides):
    data = root / "data"
    store = {
        "schema": 1,
        "example": True,
        "workouts": {
            "2099-01-01|APEX": {
                "date": "2099-01-01", "title": "APEX", "type": "class", "status": "completed",
                "status_note": None, "session_key": APEX,
                "exercises": [{"label": "A1", "name": "Row", "sets": 3, "reps": 8, "warmup": False,
                               "actuals": {"sets": [{"weight_lb": 40, "reps": 8}]}}],
            },
            "2099-01-03|Strength": {
                "date": "2099-01-03", "title": "Strength", "type": "Strength", "status": "completed",
                "status_note": None, "status_locked": True, "session_key": "2099-01-03|09:00|THIS STRENGTH",
                "exercises": [{"label": "B1", "name": "Squat", "sets": 1, "reps": 5, "warmup": False,
                               "actuals": {"sets": [{"weight_lb": 185, "reps": 5}]}}],
            },
            "2099-01-06|Upper Body": {
                "date": "2099-01-06", "title": "Upper Body", "type": "Strength", "status": "completed",
                "status_note": None, "started_at": "2099-01-06T14:00:00-06:00", "ended_at": "2099-01-06T15:00:00-06:00",
                "exercises": [
                    {"label": "A1", "name": "Bench Press", "sets": 3, "reps": 8, "warmup": False,
                     "actuals": {"sets": [{"weight_lb": 135, "reps": 8}, {"weight_lb": 135, "reps": 8}, {"weight_lb": 145, "reps": 6}]}},
                    {"label": "W", "name": "Easy Bike", "sets": 1, "warmup": True},
                ],
            },
        },
    }
    (data / "workouts.json").write_text(json.dumps(store, indent=2) + "\n")
    if overrides is None:
        path = data / "user_overrides.json"
        if path.exists():
            path.unlink()
    else:
        (data / "user_overrides.json").write_text(json.dumps(overrides, indent=2) + "\n")
    whoop = root / "whoop"
    whoop.mkdir(exist_ok=True)
    (whoop / "whoop_daily.csv").write_text("date,recovery_pct\n")
    (whoop / "whoop_sessions.csv").write_text("date,session,notes\n")
    batch = {"source": "synthetic", "workouts": [
        {"date": "2099-01-01", "title": "APEX", "status": "completed", "exercises": [
            {"label": "A1", "name": "Row", "sets": 3, "reps": 8}]},
        {"date": "2099-01-03", "title": "Strength", "status": "planned", "exercises": [
            {"label": "B1", "name": "Squat", "sets": 1, "reps": 5}]},
        {"date": "2099-01-06", "title": "Upper Body", "status": "completed", "exercises": [
            {"label": "A1", "name": "Bench Press", "sets": 3, "reps": 8},
            {"label": "W", "name": "Easy Bike", "sets": 1, "warmup": True},
        ]},
    ]}
    batch_path = root / "batch.json"
    batch_path.write_text(json.dumps(batch, indent=2) + "\n")
    return batch_path


def write_feed(root, name):
    stamp = now()
    body = "date,time,class,type,coach,status,source,feed_write\n"
    rows = [
        ("2099-01-01", "10:00", "APEX", "class", "", "RESERVED", "synthetic feed"),
        ("2099-01-03", "09:00", "THIS STRENGTH", "class", "", "RESERVED", "synthetic feed"),
        ("2099-01-06", "14:00", "Personal Training", "personal training", "Coach Example", "RESERVED", "synthetic feed"),
    ]
    for row in rows:
        body += ",".join(row) + f",{stamp}\n"
    path = root / "feeds" / f"{name}.csv"
    path.parent.mkdir(exist_ok=True)
    path.write_text(body)
    digest, size = sha(path)
    return path, digest, size, stamp


def generate(root, label, feed):
    run_cmd([sys.executable, "scripts/merge.py", str(root / "batch.json"), "--store", str(root / "data" / "workouts.json")], root, f"{label}-merge")
    out_html = root / "pages" / f"{label}.html"
    out_html.parent.mkdir(exist_ok=True)
    csv_out = root / "pages" / f"{label}-workouts.csv"
    run_cmd([
        sys.executable, "scripts/build.py",
        "--store", str(root / "data" / "workouts.json"),
        "--out", str(out_html),
        "--csv", str(csv_out),
        "--classes", str(feed),
        "--whoop", str(root / "whoop" / "whoop_daily.csv"),
    ], root, f"{label}-build")
    digest, size = sha(out_html)
    record(f"{label}-page", page=str(out_html), page_sha=digest, page_bytes=size, feed=str(feed), feed_sha=sha(feed)[0])
    return out_html, digest


def parse_html(path):
    text = Path(path).read_text(encoding="utf-8")
    dec = json.JSONDecoder()
    store = dec.raw_decode(text[text.find("const STORE = ") + len("const STORE = "):])[0]
    extra = dec.raw_decode(text[text.find("const EXTRA = ") + len("const EXTRA = "):])[0]
    return store, extra


def class_row(extra):
    for c in extra["classes"]:
        if f"{c['date']}|{c['time']}|{c['class']}" == APEX:
            return c
    return None


def set_list(store):
    out = {}
    for key, spec in SETS.items():
        w = store["workouts"][key]
        got = []
        for e in w["exercises"]:
            sets = [((s.get("weight_lb"), s.get("reps"))) for s in ((e.get("actuals") or {}).get("sets") or [])]
            if sets:
                got.append((e["label"], e["name"], sets))
        out[key] = {"status": w.get("status"), "status_locked": bool(w.get("status_locked")), "sets": got, "expected": spec}
    return out


def assert_invariants(html_path, step, allow_status):
    store, extra = parse_html(html_path)
    row = class_row(extra)
    sets = set_list(store)
    problems = []
    for key, item in sets.items():
        if item["sets"] != item["expected"]:
            problems.append(f"sets {key}")
    strength = sets["2099-01-03|Strength"]
    if strength["status"] != "completed" or not strength["status_locked"]:
        problems.append("locked strength")
    if not row or row.get("csv_status") != "RESERVED":
        problems.append("csv_status")
    if row.get("provider_cancellation_verified") is True:
        problems.append("provider true")
    if allow_status == "RESERVED" and row.get("status") != "RESERVED":
        problems.append("display status")
    if allow_status == "CANCELLED" and (row.get("status") != "CANCELLED" or row.get("cancel_source") != "user"):
        problems.append("user cancel metadata")
    record(step + "-invariants", ok=not problems, problems=problems, csv_status=row.get("csv_status") if row else None,
           status=row.get("status") if row else None, cancel_source=row.get("cancel_source") if row else None,
           provider=row.get("provider_cancellation_verified") if row else None, hidden=row.get("hidden") if row else None,
           source=row.get("source") if row else None, first_seen=row.get("first_seen") if row else None,
           last_seen=row.get("last_seen") if row else None, sets=sets)
    if problems:
        raise SystemExit(step + " invariants " + ",".join(problems))
    return row


def overrides_doc():
    return {
        "schema": 1,
        "sessions": {
            APEX: {
                "session_key": APEX, "date": "2099-01-01", "time": "10:00", "class": "APEX",
                "status": "cancelled", "attendance": "skipped", "hidden": True,
                "source": "Synthetic User", "reported_at": "2099-01-03T11:45:00-06:00",
                "provider_cancellation_verified": False,
                "note": "Synthetic user report only. Not a provider cancellation.",
            }
        },
    }


def main():
    if shutil.which("git"):
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        if head != HEAD:
            raise SystemExit(f"HEAD {head} is not the pinned proof commit")
    passed, passed_n = sha(SRC / "assembled" / "current.html")
    template_before = sha(RUNTIME / "template.html")[0]
    build_before = sha(RUNTIME / "build.py")[0]
    merge_before = sha(RUNTIME / "merge.py")[0]
    if passed != PASSED_HTML:
        raise SystemExit("assembled/current.html hash moved before the proof")
    OUT.mkdir(parents=True)
    if WORK.exists():
        shutil.rmtree(WORK)
    harness_sha, harness_n = sha(Path(__file__))
    record("pins", head=HEAD, passed_html=passed, passed_bytes=passed_n, harness_sha=harness_sha, harness_bytes=harness_n,
           template_sha=template_before, build_sha=build_before, merge_sha=merge_before)

    from playwright.sync_api import sync_playwright
    browser_requests = []
    dialogs = []

    def serve(directory):
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(directory)))
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return httpd

    def shot(page, name):
        page.locator("#app").scroll_into_view_if_needed()
        raw = OUT / "shots" / f"{name}-app.png"
        cap = OUT / "shots" / f"{name}-captioned.png"
        raw.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(raw), full_page=True)
        ts = now()
        page.evaluate("""([name, ts]) => {
          let bar = document.getElementById("harness-caption");
          if (!bar) {
            bar = document.createElement("div");
            bar.id = "harness-caption";
            document.body.insertBefore(bar, document.body.firstChild);
          }
          bar.textContent = name + " · " + ts;
          bar.setAttribute("style", "position:sticky;top:0;z-index:9999;background:#111;color:#fff;font:12px/1.4 ui-monospace,monospace;padding:8px 10px;border-bottom:3px solid #7b8cff");
        }""", [name, ts])
        page.screenshot(path=str(cap), full_page=True)
        page.evaluate("""() => { const b = document.getElementById('harness-caption'); if (b) b.remove(); }""")
        raw_sha, raw_n = sha(raw)
        cap_sha, cap_n = sha(cap)
        shots.append({"name": name, "at": ts, "app_png_sha": raw_sha, "captioned_png_sha": cap_sha})
        return {"at": ts, "app_png": raw.name, "app_sha": raw_sha, "app_bytes": raw_n, "captioned_sha": cap_sha, "captioned_bytes": cap_n}

    def click_real(page, selector):
        loc = page.locator(selector)
        loc.scroll_into_view_if_needed()
        hit = loc.evaluate("""el => {
          const r = el.getBoundingClientRect();
          const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
          return {w: r.width, h: r.height, reached: !!(top && (top === el || el.contains(top))), viewport: window.innerWidth};
        }""")
        if not hit["reached"] or hit["w"] < 20 or hit["h"] < 20 or hit["viewport"] != 390:
            raise SystemExit(f"not reachable {selector} {hit}")
        loc.click(force=False)
        return hit

    def card_state(page):
        loc = page.locator(f"[data-key='{APEX}']")
        count = loc.count()
        if count != 1:
            return {"count": count}
        return loc.evaluate("""el => ({
          count: 1, key: el.dataset.key, status: el.dataset.status, csv: el.dataset.csv,
          provider: el.dataset.provider, hidden: el.dataset.hidden, store: el.dataset.hideStore,
          cancel: el.dataset.cancelSource, parent: el.parentElement && el.parentElement.id,
          text: el.innerText
        })""")

    def storage(page):
        return page.evaluate("() => localStorage.getItem('tpDash.classHide.v1')")

    def open_page(page, port, html_path):
        rel = html_path.name
        digest, _ = sha(html_path)
        page.goto(f"http://127.0.0.1:{port}/{rel}?tab=workout&day=2099-01-01", wait_until="domcontentloaded")
        page.wait_for_selector("#app")
        width = page.evaluate("() => window.innerWidth")
        if width != 390:
            raise SystemExit(f"viewport {width}")
        return digest

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])

        def new_ctx():
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
            def route(r):
                browser_requests.append({"url": r.request.url, "method": r.request.method})
                if r.request.url.startswith("http://127.0.0.1"):
                    r.continue_()
                else:
                    r.abort()
            ctx.route("**/*", route)
            page = ctx.new_page()
            page.on("dialog", lambda d: d.dismiss() or dialogs.append(d.message))
            return ctx, page

        # Variant A
        root = WORK / "a"
        pins = copy_runtime(root)
        write_inputs(root, None)
        feed1, feed1_sha, _, feed1_at = write_feed(root, "a-initial")
        page1, page1_sha = generate(root, "a-initial", feed1)
        assert_invariants(page1, "a-initial", "RESERVED")
        httpd = serve(page1.parent)
        port = httpd.server_address[1]
        ctx, page = new_ctx()
        got = open_page(page, port, page1)
        state = card_state(page)
        record("a-start-visible", note="No user_overrides.json. APEX starts visible. This is before any Hide click.",
               page_sha=got, feed_sha=feed1_sha, feed_written=feed1_at, storage=storage(page), card=state,
               session_key=APEX, ok=state.get("hidden") == "false" and state.get("parent") == "booked" and state.get("csv") == "RESERVED")
        if not log[-1]["ok"]:
            raise SystemExit("A did not start visible")
        record("a-start-shot", **shot(page, "a-start-visible"), page_sha=got, storage=storage(page), session_key=APEX)
        hit = click_real(page, f"#booked [data-key='{APEX}'] [data-hidecls]")
        state = card_state(page)
        record("a-after-hide", hit=hit, storage=storage(page), card=state, page_sha=got, session_key=APEX,
               ok=state.get("hidden") == "true" and state.get("parent") == "hidden" and state.get("store") == "phone")
        if not log[-1]["ok"]:
            raise SystemExit("A hide did not stick")
        record("a-hide-shot", **shot(page, "a-after-hide"), page_sha=got, storage=storage(page), session_key=APEX)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector("#app")
        state = card_state(page)
        record("a-after-reload", storage=storage(page), card=state, page_sha=sha(page1)[0], session_key=APEX,
               ok=state.get("hidden") == "true" and APEX in (storage(page) or ""))
        if not log[-1]["ok"]:
            raise SystemExit("A reload lost the hide")
        record("a-reload-shot", **shot(page, "a-after-reload"), page_sha=sha(page1)[0], storage=storage(page), session_key=APEX)
        feed2, feed2_sha, _, feed2_at = write_feed(root, "a-fresh-reserved")
        if feed2_sha == feed1_sha:
            raise SystemExit("fresh feed hash did not change")
        page2, page2_sha = generate(root, "a-rebuilt", feed2)
        assert_invariants(page2, "a-rebuilt", "RESERVED")
        if (root / "data" / "user_overrides.json").exists():
            raise SystemExit("variant A created a canonical override file")
        got = open_page(page, port, page2)
        state = card_state(page)
        record("a-after-rebuild-same-browser", note="Real build.py and merge.py reran on a new RESERVED feed. Same browser storage.",
               page_sha=got, previous_page_sha=page1_sha, feed_sha=feed2_sha, previous_feed_sha=feed1_sha, feed_written=feed2_at,
               storage=storage(page), card=state, session_key=APEX,
               ok=state.get("hidden") == "true" and state.get("store") == "phone" and state.get("csv") == "RESERVED" and state.get("status") == "RESERVED")
        if not log[-1]["ok"]:
            raise SystemExit("A rebuild resurrected the row")
        record("a-rebuild-shot", **shot(page, "a-after-rebuild"), page_sha=got, storage=storage(page), session_key=APEX, feed_sha=feed2_sha)
        hit = click_real(page, f"#hidden [data-key='{APEX}'] [data-undocls]")
        state = card_state(page)
        record("a-after-undo", hit=hit, storage=storage(page), card=state, page_sha=got, session_key=APEX,
               ok=state.get("hidden") == "false" and state.get("parent") == "booked" and state.get("status") == "RESERVED" and state.get("provider") == "false")
        if not log[-1]["ok"]:
            raise SystemExit("A undo did not show the row")
        record("a-undo-shot", **shot(page, "a-after-undo"), page_sha=got, storage=storage(page), session_key=APEX)
        ctx.close()
        httpd.shutdown()

        # Variant B
        root = WORK / "b"
        copy_runtime(root)
        write_inputs(root, overrides_doc())
        feed1, feed1_sha, _, feed1_at = write_feed(root, "b-initial")
        page1, page1_sha = generate(root, "b-initial", feed1)
        row = assert_invariants(page1, "b-initial", "CANCELLED")
        if row.get("hidden") is not True or row.get("provider_cancellation_verified") is not False:
            raise SystemExit("B build did not bake the shared hide")
        canon = sha(root / "data" / "user_overrides.json")
        httpd = serve(page1.parent)
        port = httpd.server_address[1]
        empty, empty_page = new_ctx()
        got = open_page(empty_page, port, page1)
        state = card_state(empty_page)
        record("b-empty-browser-built-hide",
               note="Setup only. The row is already hidden by the shared file consumed by build.py. This is not a Hide click.",
               page_sha=got, feed_sha=feed1_sha, feed_written=feed1_at, storage=storage(empty_page), card=state,
               canonical_sha=canon[0], session_key=APEX,
               ok=storage(empty_page) in (None, "null") and state.get("hidden") == "true" and state.get("store") == "built" and state.get("provider") == "false")
        if not log[-1]["ok"]:
            raise SystemExit("empty browser did not follow the shared hide")
        record("b-empty-shot", **shot(empty_page, "b-empty-built-hide"), page_sha=got, storage=storage(empty_page), session_key=APEX)
        empty.close()

        ctx, page = new_ctx()
        got = open_page(page, port, page1)
        record("b-before-undo", note="Same built page. Undo is required before a Hide click because the row is not visible yet.",
               storage=storage(page), card=card_state(page), page_sha=got, session_key=APEX)
        hit = click_real(page, f"#hidden [data-key='{APEX}'] [data-undocls]")
        state = card_state(page)
        record("b-local-false-overrides-built-true", hit=hit, storage=storage(page), card=state, page_sha=got,
               canonical_sha=sha(root / "data" / "user_overrides.json")[0], session_key=APEX,
               ok=state.get("hidden") == "false" and state.get("store") == "phone" and state.get("status") == "CANCELLED" and state.get("provider") == "false" and sha(root / "data" / "user_overrides.json")[0] == canon[0])
        if not log[-1]["ok"]:
            raise SystemExit("local false did not override the built hide")
        record("b-local-false-shot", **shot(page, "b-local-false-visible"), page_sha=got, storage=storage(page), session_key=APEX)
        hit = click_real(page, f"#booked [data-key='{APEX}'] [data-hidecls]")
        state = card_state(page)
        record("b-after-hide-click", note="This Hide click happens only after Undo showed the row.", hit=hit, storage=storage(page), card=state, page_sha=got, session_key=APEX,
               ok=state.get("hidden") == "true" and state.get("store") == "phone")
        if not log[-1]["ok"]:
            raise SystemExit("B hide click failed")
        record("b-hide-shot", **shot(page, "b-after-hide"), page_sha=got, storage=storage(page), session_key=APEX)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector("#app")
        state = card_state(page)
        record("b-after-reload", storage=storage(page), card=state, page_sha=sha(page1)[0], session_key=APEX, ok=state.get("hidden") == "true")
        if not log[-1]["ok"]:
            raise SystemExit("B reload lost the hide")
        record("b-reload-shot", **shot(page, "b-after-reload"), page_sha=sha(page1)[0], storage=storage(page), session_key=APEX)
        feed2, feed2_sha, _, feed2_at = write_feed(root, "b-fresh-reserved")
        if feed2_sha == feed1_sha:
            raise SystemExit("B fresh feed hash did not change")
        page2, page2_sha = generate(root, "b-rebuilt", feed2)
        assert_invariants(page2, "b-rebuilt", "CANCELLED")
        if sha(root / "data" / "user_overrides.json")[0] != canon[0]:
            raise SystemExit("rebuild changed the canonical override file")
        got = open_page(page, port, page2)
        state = card_state(page)
        record("b-after-rebuild-same-browser", page_sha=got, previous_page_sha=page1_sha, feed_sha=feed2_sha, previous_feed_sha=feed1_sha,
               feed_written=feed2_at, storage=storage(page), card=state, canonical_sha=canon[0], session_key=APEX,
               ok=state.get("hidden") == "true" and state.get("csv") == "RESERVED" and state.get("provider") == "false")
        if not log[-1]["ok"]:
            raise SystemExit("B rebuild did not keep the phone hide")
        record("b-rebuild-shot", **shot(page, "b-after-rebuild"), page_sha=got, storage=storage(page), session_key=APEX, feed_sha=feed2_sha)
        hit = click_real(page, f"#hidden [data-key='{APEX}'] [data-undocls]")
        state = card_state(page)
        record("b-after-undo-visible", hit=hit, storage=storage(page), card=state, page_sha=got, canonical_sha=sha(root / "data" / "user_overrides.json")[0],
               session_key=APEX, ok=state.get("hidden") == "false" and state.get("parent") == "booked" and state.get("status") == "CANCELLED" and sha(root / "data" / "user_overrides.json")[0] == canon[0])
        if not log[-1]["ok"]:
            raise SystemExit("B undo did not reveal the row")
        record("b-undo-shot", **shot(page, "b-after-undo"), page_sha=got, storage=storage(page), session_key=APEX)
        ctx.close()

        fresh, fresh_page = new_ctx()
        got = open_page(fresh_page, port, page2)
        state = card_state(fresh_page)
        record("b-second-empty-browser", note="A different empty browser still follows the built shared hide. The phone Undo did not change the file.",
               page_sha=got, storage=storage(fresh_page), card=state, canonical_sha=sha(root / "data" / "user_overrides.json")[0], session_key=APEX,
               ok=storage(fresh_page) in (None, "null") and state.get("hidden") == "true" and state.get("store") == "built" and state.get("provider") == "false" and state.get("status") == "CANCELLED")
        if not log[-1]["ok"]:
            raise SystemExit("second empty browser did not follow the built hide")
        record("b-second-empty-shot", **shot(fresh_page, "b-second-empty-built-hide"), page_sha=got, storage=storage(fresh_page), session_key=APEX)
        fresh.close()
        httpd.shutdown()
        browser.close()

    passed_after, _ = sha(SRC / "assembled" / "current.html")
    template_after = sha(RUNTIME / "template.html")[0]
    record("unchanged-artifact", passed_html_after=passed_after, template_after=template_after,
           build_after=sha(RUNTIME / "build.py")[0], merge_after=sha(RUNTIME / "merge.py")[0],
           ok=passed_after == PASSED_HTML and template_after == template_before and sha(RUNTIME / "build.py")[0] == build_before and sha(RUNTIME / "merge.py")[0] == merge_before and not dialogs)
    # identical app pixels
    by_raw = {}
    for item in shots:
        by_raw.setdefault(item["app_png_sha"], []).append(item["name"])
    identical = {k: v for k, v in by_raw.items() if len(v) > 1}
    off = [r for r in browser_requests if not r["url"].startswith("http://127.0.0.1")]
    summary = {
        "head": HEAD,
        "passed_html_unchanged": passed_after == PASSED_HTML,
        "harness_sha": harness_sha,
        "pins": pins,
        "identical_app_pngs": identical,
        "off_machine_requests": off,
        "dialogs": dialogs,
        "steps": log,
        "shots": shots,
    }
    (OUT / "sequence.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("PROOF DONE", "identical", identical, "off", off)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "sequence-partial.json").write_text(json.dumps({"steps": log, "shots": shots}, indent=2, default=str) + "\n")
        raise
