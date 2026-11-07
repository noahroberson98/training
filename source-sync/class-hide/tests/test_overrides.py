"""Synthetic override consumption. No network, no provider, no live store."""
import json, os, sys, tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "runtime"))
import build
import merge

FIX = HERE / "fixtures"
ok = True

def check(c, m):
    global ok
    print(("PASS " if c else "FAIL ") + m)
    ok = ok and bool(c)

feed = json.loads((FIX / "feed_current.json").read_text())["reservations"]
hist = json.loads((FIX / "class_history_before.json").read_text())
overrides = json.loads((FIX / "user_overrides.json").read_text())["sessions"]
now = datetime(2099, 1, 4, 12, 0, 0)

with tempfile.TemporaryDirectory() as d:
    hist_path = os.path.join(d, "class_history.json")
    Path(hist_path).write_text(json.dumps(hist))
    rows = build.update_class_history(feed, hist_path=hist_path, now=now, overrides=overrides)
    by = {f"{r['date']}|{r['time']}|{r['class']}": r for r in rows}
    stale = by["2099-01-01|10:00|APEX"]
    missing = by["2099-01-02|10:00|APEX"]
    other = by["2099-01-03|09:00|THIS STRENGTH"]
    check(stale["status"] == "CANCELLED" and stale["hidden"] is True, "stale reserved feed stays hidden and user-cancelled")
    check(stale["csv_status"] == "RESERVED" and stale["source"] == "synthetic feed", "stale feed keeps reserved status and source")
    check(stale["cancel_source"] == "user" and stale["provider_cancellation_verified"] is False, "user cancel is not a provider confirmation")
    check(missing["status"] == "CANCELLED" and missing["hidden"] is True, "missing feed row stays hidden and user-cancelled")
    check(missing["status"] != "COMPLETED" and missing["csv_status"] == "RESERVED", "missing row is not inferred completed")
    check(other["status"] == "RESERVED" and not other.get("hidden"), "unrelated booking stays reserved and visible")
    undo = json.loads(json.dumps(overrides))
    undo["2099-01-01|10:00|APEX"]["hidden"] = False
    Path(hist_path).write_text(json.dumps(by))
    rows = build.update_class_history(feed, hist_path=hist_path, now=now, overrides=undo)
    by = {f"{r['date']}|{r['time']}|{r['class']}": r for r in rows}
    back = by["2099-01-01|10:00|APEX"]
    check(back["hidden"] is False and back["status"] == "CANCELLED" and back["csv_status"] == "RESERVED", "undo shows the row without restoring a provider reservation")
    bare = json.loads((FIX / "class_history_before.json").read_text())
    bare_path = os.path.join(d, "bare.json")
    Path(bare_path).write_text(json.dumps(bare))
    bare_rows = build.update_class_history(feed, hist_path=bare_path, now=now, overrides=None)
    bare_by = {f"{r['date']}|{r['time']}|{r['class']}": r for r in bare_rows}
    check(bare_by["2099-01-02|10:00|APEX"]["status"] == "COMPLETED", "without an override, a past missing row still follows the existing completed rule")

store = {"schema": 1, "workouts": {"2099-01-01|APEX": {
    "date": "2099-01-01", "title": "APEX", "type": "Strength", "status": "planned",
    "status_note": None, "session_key": "2099-01-01|10:00|APEX",
    "exercises": [{"label": "A1", "name": "Row", "sets": 3, "reps": 8, "actuals": {"sets": [{"weight_lb": 40, "reps": 8}]}}]}}}
batch = {"workouts": [{"date": "2099-01-01", "title": "APEX", "status": "completed", "exercises": []}]}
merge.merge(store, batch, "synthetic", overrides=overrides)
w = store["workouts"]["2099-01-01|APEX"]
check(w["status"] == "skipped" and w["user_cancel_source"] == "user" and w["provider_cancellation_verified"] is False, "merge does not complete a user-cancelled session")
check(w["exercises"][0]["actuals"]["sets"][0]["weight_lb"] == 40, "merge keeps the logged set")
locked = {"schema": 1, "workouts": {"2099-01-03|Strength": {
    "date": "2099-01-03", "title": "Strength", "type": "Strength", "status": "completed",
    "status_note": None, "status_locked": True, "session_key": "2099-01-03|09:00|THIS STRENGTH",
    "exercises": [{"label": "B1", "name": "Squat", "sets": 1}]}}}
merge.merge(locked, {"workouts": [{"date": "2099-01-03", "title": "Strength", "status": "planned", "exercises": []}]}, "synthetic", overrides={
    "2099-01-03|09:00|THIS STRENGTH": {"status": "cancelled", "attendance": "skipped", "hidden": True, "provider_cancellation_verified": False}})
check(locked["workouts"]["2099-01-03|Strength"]["status"] == "completed" and locked["workouts"]["2099-01-03|Strength"]["status_locked"] is True, "a locked workout status is not rewritten")
plain = {"schema": 1, "workouts": {}}
merge.merge(plain, {"workouts": [{"date": "2099-01-04", "title": "Upper Body", "status": "completed", "exercises": []}]}, "synthetic")
check(plain["workouts"]["2099-01-04|Upper Body"]["status"] == "completed", "a workout with no override still merges")
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
