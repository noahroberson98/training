"""Fill the real template with an explicitly synthetic dataset.

Uses update_class_history and merge from the patched runtime. Does not read a
live store, does not call a provider, and does not write user_overrides.json
from the browser. The canonical file is an input to this build only.
"""
import copy
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "runtime"))
import build  # noqa: E402
import merge  # noqa: E402

FIX = HERE / "fixtures"
OUT = HERE / "assembled"
NOW = datetime(2099, 1, 4, 12, 0, 0)
BUILT = "Jan 3, 2099, 11:46 AM CT"
PT = {
    "date": "2099-01-06",
    "time": "14:00",
    "class": "Personal Training",
    "type": "personal training",
    "coach": "Coach Example",
    "status": "RESERVED",
    "source": "synthetic feed",
}


def load_feed(names):
    rows = json.loads((FIX / "feed_current.json").read_text())["reservations"]
    by = {f"{r['date']}|{r['time']}|{r['class']}": r for r in rows}
    return [dict(by[n]) for n in names] + [dict(PT)]


def base_store():
    def ex(label, name, sets, reps, actuals, warmup=False):
        row = {"label": label, "name": name, "sets": sets, "reps": reps, "warmup": warmup}
        if actuals is not None:
            row["actuals"] = {"sets": actuals}
        return row

    return {
        "schema": 1,
        "example": True,
        "workouts": {
            "2099-01-01|APEX": {
                "date": "2099-01-01",
                "title": "APEX",
                "type": "class",
                "status": "planned",
                "status_note": None,
                "session_key": "2099-01-01|10:00|APEX",
                "exercises": [ex("A1", "Row", 3, 8, [{"weight_lb": 40, "reps": 8}])],
            },
            "2099-01-03|Strength": {
                "date": "2099-01-03",
                "title": "Strength",
                "type": "Strength",
                "status": "completed",
                "status_note": None,
                "status_locked": True,
                "session_key": "2099-01-03|09:00|THIS STRENGTH",
                "exercises": [ex("B1", "Squat", 1, 5, [{"weight_lb": 185, "reps": 5}])],
            },
            "2099-01-06|Upper Body": {
                "date": "2099-01-06",
                "title": "Upper Body",
                "type": "Strength",
                "status": "completed",
                "status_note": None,
                "started_at": "2099-01-06T14:00:00-06:00",
                "ended_at": "2099-01-06T15:00:00-06:00",
                "exercises": [
                    ex("A1", "Bench Press", 3, 8, [
                        {"weight_lb": 135, "reps": 8},
                        {"weight_lb": 135, "reps": 8},
                        {"weight_lb": 145, "reps": 6},
                    ]),
                    ex("W", "Easy Bike", 1, None, None, warmup=True),
                ],
            },
        },
    }


def merged_store(overrides):
    store = base_store()
    batch = {"workouts": [
        {"date": "2099-01-01", "title": "APEX", "status": "completed", "exercises": [
            {"label": "A1", "name": "Row", "sets": 3, "reps": 8}]},
        {"date": "2099-01-03", "title": "Strength", "status": "planned", "exercises": [
            {"label": "B1", "name": "Squat", "sets": 1, "reps": 5}]},
        {"date": "2099-01-06", "title": "Upper Body", "status": "completed", "exercises": [
            {"label": "A1", "name": "Bench Press", "sets": 3, "reps": 8},
            {"label": "W", "name": "Easy Bike", "sets": 1, "warmup": True},
        ]},
    ]}
    merge.merge(store, batch, "synthetic-fixture", overrides=overrides)
    return store


def classes_for(feed, overrides):
    hist = json.loads((FIX / "class_history_before.json").read_text())
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "class_history.json")
        Path(path).write_text(json.dumps(hist))
        return build.update_class_history(feed, hist_path=path, now=NOW, overrides=overrides)


def fill(template, store, classes, fixture):
    extra = {
        "target_overrides": {},
        "features": {"cancel_relay": False},
        "classes": classes,
        "recovery": {},
        "workout_whoop": {},
        "fixture": fixture,
        "persistence": {
            "phone": "localStorage key tpDash.classHide.v1 on this browser only",
            "canonical_file": "data/user_overrides.json",
            "written_by_this_page": False,
            "cross_device": False,
        },
    }
    tpl = re.sub(r"/\*RELAY\*/.*?/\*/RELAY\*/", "", template, flags=re.S)
    disp = copy.deepcopy(store)
    for w in disp.get("workouts", {}).values():
        w["title"] = build.display_title(w.get("title", ""))
    data = json.dumps(disp, ensure_ascii=False).replace("</", "<\\/")
    packed = json.dumps(extra, ensure_ascii=False).replace("</", "<\\/")
    return tpl.replace("/*__DATA__*/null", data).replace("/*__EXTRA__*/null", packed).replace("__BUILT__", BUILT)


def main():
    overrides = json.loads((FIX / "user_overrides.json").read_text())["sessions"]
    template = (HERE / "runtime" / "template.html").read_text(encoding="utf-8")
    if "/*__DATA__*/null" not in template or "/*__EXTRA__*/null" not in template:
        raise SystemExit("template placeholders missing")
    store = merged_store(overrides)
    scenarios = {
        "current": ["2099-01-01|10:00|APEX", "2099-01-03|09:00|THIS STRENGTH"],
        "reimport-reserved": ["2099-01-01|10:00|APEX", "2099-01-03|09:00|THIS STRENGTH"],
        "reimport-missing": ["2099-01-03|09:00|THIS STRENGTH"],
    }
    OUT.mkdir(exist_ok=True)
    proof = {"built": BUILT, "synthetic": True, "scenarios": {}}
    for name, keys in scenarios.items():
        classes = classes_for(load_feed(keys), overrides)
        html = fill(template, store, classes, name)
        path = OUT / f"{name}.html"
        path.write_text(html, encoding="utf-8")
        by = {f"{c['date']}|{c['time']}|{c['class']}": c for c in classes}
        proof["scenarios"][name] = {
            "bytes": path.stat().st_size,
            "classes": {k: {f: by[k].get(f) for f in (
                "status", "csv_status", "hidden", "cancel_source", "source",
                "provider_cancellation_verified")} for k in by},
        }
    proof["workouts"] = {
        k: {"status": w.get("status"), "status_locked": bool(w.get("status_locked")),
            "user_cancel_source": w.get("user_cancel_source"),
            "provider_cancellation_verified": w.get("provider_cancellation_verified"),
            "sets": [[s.get("weight_lb"), s.get("reps")] for e in w.get("exercises", []) for s in ((e.get("actuals") or {}).get("sets") or [])]}
        for k, w in store["workouts"].items()
    }
    log = HERE / "logs"
    log.mkdir(exist_ok=True)
    (log / "assemble.json").write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
