#!/usr/bin/env python3
"""Build dashboard.html (self-contained) and the flat CSV from data/workouts.json.

  python3 scripts/build.py                 # dashboard.html + CSV
  python3 scripts/build.py --screenshot    # also dashboard.png (mobile 430x932) + dashboard-desktop.png
Options: --store, --out, --csv, --png, --desktop-png, --day YYYY-MM-DD (day shown in screenshots)
"""
import copy
import re
import argparse, csv, json, os, shutil, subprocess, sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from common import actual_sets, apply_user_class_override, eff_date, fmt_dur, load_user_overrides, provider_feed_status  # noqa: E402
from whoop_pair import load_sessions, pair  # noqa: E402

CSV_COLS = ["date", "workout_title", "status", "label", "exercise", "sets", "reps", "duration",
            "planned_weight_lb", "other_load", "coach_note", "actual_weight_lb", "actual_reps", "actual_notes"]


def blank(v):
    return "" if v is None else v


def write_csv(store, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_COLS)
        for wk in sorted(store["workouts"].values(), key=lambda x: (eff_date(x), x["title"])):
            for e in wk["exercises"]:
                sets = actual_sets(e)
                wts = ",".join("" if s.get("weight_lb") is None else f"{s['weight_lb']:g}" for s in sets)
                reps = ",".join(str(s["reps"]) if s.get("reps") is not None else
                                (fmt_dur(s["duration_s"]) if s.get("duration_s") is not None else
                                 (f"{s['distance_m']:g}m" if s.get("distance_m") is not None else "")) for s in sets)
                w.writerow([eff_date(wk), wk["title"], wk["status"], e["label"], e["name"],
                            blank(e.get("sets")), blank(e.get("reps")), fmt_dur(e.get("duration_s")),
                            blank(e.get("weight_lb")), blank(e.get("other_load")), blank(e.get("note")),
                            wts.strip(",") and wts, reps, blank((e.get("actuals") or {}).get("notes"))])


def find_chrome():
    for c in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        p = shutil.which(c)
        if p:
            return p
    return None


def screenshot(html, png, width, height, query="", scale=1):
    url = "file://" + os.path.abspath(html) + (("?" + query) if query else "")
    chrome = find_chrome()
    if chrome:
        cmd = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
               f"--window-size={width},{height}", f"--force-device-scale-factor={scale}",
               "--virtual-time-budget=3000", f"--screenshot={os.path.abspath(png)}", url]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and os.path.exists(png):
            return True
        print(r.stderr[-800:], file=sys.stderr)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": width, "height": height}, device_scale_factor=scale)
            pg.goto(url)
            pg.screenshot(path=png)
            b.close()
        return True
    except Exception as ex:
        print(f"screenshot skipped (no headless browser): {ex}", file=sys.stderr)
        return False


FD = "/workspace/fitness-dashboard"


def read_classes(path):
    """THIS Gym reservations CSV: date,time,class,type,coach,status,source."""
    if not path or not os.path.exists(path):
        return []
    out = []
    mtime = datetime.fromtimestamp(os.path.getmtime(path)).replace(microsecond=0)
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            if not r.get("date"):
                continue
            out.append({"date": r["date"], "time": r.get("time", ""), "class": r.get("class", ""),
                        "type": r.get("type", ""), "coach": r.get("coach", ""),
                        "status": (r.get("status") or "").upper(), "source": r.get("source", ""), "_mtime": mtime})
    return sorted(out, key=lambda c: (c["date"], c["time"]))


def read_recovery(path):
    """WHOOP daily CSV -> {date: recovery_pct}."""
    if not path or not os.path.exists(path):
        return {}
    rec = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                rec[r["date"].strip()] = round(float(r["recovery_pct"]))
            except (KeyError, ValueError, TypeError, AttributeError):
                pass
    return rec


CLASS_HIST = os.path.join(ROOT, "data", "class_history.json")


def _mins(t):
    m = re.match(r"^(\d{1,2}):(\d{2})", t or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


CANCEL_REQ = os.path.join(ROOT, "data", "cancel_requests.json")


def load_cancels(path=CANCEL_REQ):
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f).get("requests", {})
    return {}


def _read_time(c, fallback):
    """When PushPress was actually read: from the CSV source column ('... 2026-10-29 5:35 AM CT'),
    else the CSV file's mtime (passed as fallback)."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})\s*([AP]M)", c.get("source", ""), re.I)
    if m:
        h = int(m.group(2)) % 12 + (12 if m.group(4).upper() == "PM" else 0)
        return datetime.strptime(m.group(1), "%Y-%m-%d").replace(hour=h, minute=int(m.group(3)))
    return fallback


def update_class_history(current, hist_path=CLASS_HIST, now=None, cancels=None, overrides=None):
    """Durable THIS Gym class history (the reservations CSV only lists upcoming ones).
    Every class seen is recorded; booked classes whose start passed and that left the CSV become
    COMPLETED; a CANCELLED status in the CSV is kept as CANCELLED. Returns the merged class list."""
    now = now or datetime.now()
    hist = {}
    if hist_path and os.path.exists(hist_path):
        with open(hist_path) as f:
            hist = json.load(f)
    seen = set()
    for c in current:
        k = f"{c['date']}|{c['time']}|{c['class']}"
        seen.add(k)
        prev = hist.get(k, {})
        e = dict(prev, **{x: c[x] for x in ("date", "time", "class", "type", "coach", "source") if c.get(x) or x not in prev})
        baseline, basis = provider_feed_status(prev, c.get("status"), (overrides or {}).get(k))
        e["feed_status"] = c.get("status")
        e["csv_status"] = baseline
        e["provider_status"] = baseline
        e["provider_status_basis"] = basis
        e["status"] = baseline if str(baseline).lower() != "unknown" else (prev.get("status") or "unknown")
        seen_at = _read_time(c, c.get("_mtime") or now).isoformat(timespec="seconds")
        e.setdefault("first_seen", seen_at)
        if seen_at > e.get("last_seen", ""):
            e["last_seen"] = seen_at
        hist[k] = e
    cancels = cancels or {}
    for k, e in hist.items():
        req = cancels.get(k) or {}
        e.pop("cancel_requested", None)
        if req.get("status") == "done":          # This Gym Fitness confirmed
            e["status"] = "CANCELLED"; e["cancel_source"] = "confirmed"; continue
        if k in seen:
            if req.get("status") == "requested":
                e["cancel_requested"] = req.get("requested_at", True)   # still booked, small note
            continue
        # User-confirmed or CSV cancel: never auto-flip to COMPLETED when the class left the CSV
        if e.get("cancel_source") in ("csv", "confirmed") and req.get("status") != "declined":
            e["status"] = "CANCELLED"
            continue
        if req.get("status") == "requested":
            try:
                start = datetime.strptime(f"{e['date']} {e['time'] or '00:00'}", "%Y-%m-%d %H:%M")
            except ValueError:
                start = None
            if start and now < start:   # requested and left the CSV before it started -> cancelled in the app
                e["status"] = "CANCELLED"; e["cancel_source"] = "csv"; continue
        try:
            start = datetime.strptime(f"{e['date']} {e['time'] or '00:00'}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        last = (e.get("csv_status") or "").upper()
        if "CANCEL" in last:
            e["status"] = "CANCELLED"
        elif start <= now and "WAIT" not in last:
            e["status"] = "COMPLETED"
        elif start <= now:
            e["status"] = "MISSED"   # was only waitlisted; can't assume attended
    for k, ov in (overrides or {}).items():
        e = hist.get(k)
        if not e:
            continue  # absence is not a new class and is not a cancellation
        apply_user_class_override(e, ov)
    if hist_path:
        tmp = hist_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(hist, f, indent=1, sort_keys=True)
        os.replace(tmp, hist_path)
    return sorted(hist.values(), key=lambda c: (c["date"], c["time"]))

def attach_posted(classes, path):
    """Attach THIS Gym posted workout text only on an exact date + time + class-name match. Never guess."""
    try:
        posted = json.load(open(path)).get("workouts", [])
    except (OSError, ValueError):
        posted = []
    idx = {}
    for w in posted:
        if w.get("date") and w.get("time_ct") and w.get("class_name"):
            idx.setdefault((w["date"], w["time_ct"], w["class_name"].strip().upper()), []).append(w)
    today = date.today().isoformat()
    for c in classes:
        c.pop("posted", None); c.pop("posted_coach", None)
        if (c.get("type") or "").lower() not in ("class",) and "personal training" in (c.get("class") or "").lower():
            continue
        m = idx.get((c["date"], c.get("time"), (c.get("class") or "").strip().upper()), [])
        if len(m) == 1 and (m[0].get("workout") or "").strip():
            c["posted"] = m[0]["workout"].strip()
            if m[0].get("coach") and c.get("coach") and m[0]["coach"].split()[0].lower() != c["coach"].split()[0].lower():
                c["posted_coach"] = m[0]["coach"]
        elif c["date"] >= today:
            c["posted"] = ""   # booked, nothing posted yet


def display_title(t):
    t = re.sub(r"\s*·\s*planned by .*$", "", t or "", flags=re.I).strip()
    return {"Lower": "Lower Body", "Upper": "Upper Body"}.get(t, t)


def build(store_path, out, csv_path, classes_csv=os.path.join(FD, "thisgym_reservations.csv"),
          whoop_csv=os.path.join(FD, "whoop_daily.csv"), class_hist=CLASS_HIST):
    with open(store_path) as f:
        store = json.load(f)
    sessions = load_sessions(os.path.join(os.path.dirname(whoop_csv or FD) or FD, "whoop_sessions.csv"), whoop_csv)
    classes = update_class_history(read_classes(classes_csv), hist_path=class_hist, cancels=load_cancels(),
                                   overrides=load_user_overrides(os.path.join(ROOT, "data", "user_overrides.json")))
    attach_posted(classes, os.path.join(FD, "thisgym_workouts.json"))
    items = []
    for c in classes:
        c.pop("whoop", None); c.pop("whoop_match", None)
        if c["status"] == "COMPLETED":
            items.append({"id": "class:" + f"{c['date']}|{c['time']}|{c['class']}", "date": c["date"],
                          "time": c["time"], "kind": "class", "name": c["class"], "type": c.get("type", ""), "_c": c})
    for k, w in store.get("workouts", {}).items():
        if w.get("status") == "completed":
            items.append({"id": "workout:" + k, "date": w.get("completed_date") or eff_date(w),
                          "time": w.get("completed_time", ""), "kind": "workout", "name": w.get("title", ""),
                          "type": w.get("type", ""), "_k": k})
    pairs = pair(items, sessions)
    workout_whoop = {}
    for it in items:
        if it["id"] not in pairs:
            continue
        sess, match = pairs[it["id"]]
        if "_c" in it:
            it["_c"]["whoop"], it["_c"]["whoop_match"] = sess, match
        else:
            workout_whoop[it["_k"]] = dict(sess, match=match)
    feats = {"cancel_relay": False}
    fp = os.path.join(ROOT, "data", "features.json")
    if os.path.exists(fp):
        feats.update(json.load(open(fp)))
    tov = {}
    tp = os.path.join(ROOT, "data", "target_overrides.json")
    if os.path.exists(tp):
        tov = {k: v for k, v in json.load(open(tp)).items() if not k.startswith("_")}
    extra = {"target_overrides": tov, "features": feats, "classes": classes, "recovery": read_recovery(whoop_csv), "workout_whoop": workout_whoop}
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    if not feats.get("cancel_relay"):   # strip the issue-link flow entirely when the relay is off
        tpl = re.sub(r"/\*RELAY\*/.*?/\*/RELAY\*/", "", tpl, flags=re.S)
    disp = copy.deepcopy(store)   # UI-only title cleanup: no bot names, full body-part names
    for w in disp.get("workouts", {}).values():
        w["title"] = display_title(w.get("title", ""))
    data = json.dumps(disp, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace("/*__DATA__*/null", data).replace(
        "/*__EXTRA__*/null", json.dumps(extra, ensure_ascii=False).replace("</", "<\\/")).replace("__BUILT__", datetime.now().strftime("%b %-d, %Y %-I:%M %p CT"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    write_csv(store, csv_path)
    return store


def tp_freshness_warning(max_hours=6):
    """Warn (stderr) when the newest TrainingPeaks batch read is stale, so an on-demand
    update re-reads TP live instead of reusing the morning batch (11/1 miss)."""
    import glob
    from datetime import datetime as _dt, timezone as _tz
    best = None
    for f in glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "batches", "*.json")):
        try:
            ra = json.load(open(f)).get("read_at")
            t = _dt.fromisoformat(ra) if ra else None
        except Exception:
            continue
        if t and (best is None or t > best[0]):
            best = (t, os.path.basename(f))
    if best is None:
        return
    age = (_dt.now(_tz.utc) - best[0]).total_seconds() / 3600
    if age > max_hours:
        print(f"WARNING: newest TrainingPeaks read is {age:.1f} h old ({best[1]}); re-read TrainingPeaks live before telling User what is planned", file=sys.stderr)


def main():
    tp_freshness_warning()
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=os.path.join(ROOT, "data", "workouts.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "dashboard.html"))
    ap.add_argument("--csv", default="/workspace/fitness-dashboard/trainingpeaks_workouts.csv")
    ap.add_argument("--screenshot", action="store_true")
    ap.add_argument("--png", default=os.path.join(ROOT, "dashboard.png"))
    ap.add_argument("--desktop-png", default=os.path.join(ROOT, "dashboard-desktop.png"))
    ap.add_argument("--day", default=date.today().isoformat())
    ap.add_argument("--classes", default=os.path.join(FD, "thisgym_reservations.csv"))
    ap.add_argument("--whoop", default=os.path.join(FD, "whoop_daily.csv"))
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    store = build(a.store, a.out, a.csv, a.classes, a.whoop)
    if not a.quiet:
        print(f"read {len(read_classes(a.classes))} THIS Gym classes, {len(read_recovery(a.whoop))} WHOOP days")
        n_ex = sum(len(w["exercises"]) for w in store["workouts"].values())
        print(f"wrote {a.out} ({len(store['workouts'])} workouts, {n_ex} exercises)")
        print(f"wrote {a.csv}")
    if a.screenshot:
        if screenshot(a.out, a.png, 430, 932, f"day={a.day}", scale=2):
            print(f"wrote {a.png}")
        if screenshot(a.out, a.desktop_png, 1440, 1000, f"day={a.day}", scale=1):
            print(f"wrote {a.desktop_png}")


if __name__ == "__main__":
    main()
