#!/usr/bin/env python3
"""Merge a batch of TrainingPeaks workouts into data/workouts.json.

Usage: python3 scripts/merge.py BATCH.json [--store data/workouts.json]

BATCH.json is either
  * a TrainingPeaks batch: {"source": ..., "workouts": [ ... ]}, or
  * an actuals export downloaded from dashboard.html
    ({"kind": "actuals_export", "actuals": {...}}); the logged weight/reps/notes
    are folded into the matching exercises' `actuals`.

Rules (idempotent, append-only):
  * Workouts are keyed by their original TrainingPeaks "YYYY-MM-DD|Title". Nothing is ever deleted.
  * Moves made with log.py --move (field `moved_to`) are kept: a later batch with the same
    original date+title updates the plan but never moves it back.
  * Re-merging identical data changes nothing (no new revision, same file).
  * When a workout's prescription/status changes, the previous version is
    pushed onto that workout's `revisions` list before being updated.
  * Recorded actuals are never overwritten by null in a later batch, and a
    batch saying "planned" never reverts a completed/skipped status.
"""
import argparse, copy, hashlib, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import actual_sets, eff_date, fill_per_plan, hold_user_workout_overrides, load_user_overrides  # noqa: E402
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STORE = os.path.join(ROOT, "data", "workouts.json")
STATUSES = {"planned", "completed", "skipped"}


def parse_duration_s(e):
    """Accept duration_s or TrainingPeaks duration "HH:MM:SS" / "MM:SS"."""
    def num(v):
        if v is None or v == "":
            return None
        f = float(v)
        return int(f) if f.is_integer() else f
    ds = num(e.get("duration_s"))
    if ds is not None:
        return ds
    raw = e.get("duration")
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return num(raw)
    s = str(raw).strip()
    if s.isdigit():
        return int(s)
    parts = s.split(":")
    try:
        parts = [int(x) for x in parts]
    except ValueError:
        return None
    if len(parts) == 3:
        h, m, sec = parts
        return h * 3600 + m * 60 + sec
    if len(parts) == 2:
        m, sec = parts
        return m * 60 + sec
    return None


def norm_exercise(e):
    def num(v):
        if v is None or v == "":
            return None
        f = float(v)
        return int(f) if f.is_integer() else f
    label = str(e.get("label", "")).strip()
    return {
        "label": label,
        "block": e.get("block") or (label[:1] if label else None),
        "name": str(e["name"]).strip(),
        "sets": num(e.get("sets")),
        "reps": num(e.get("reps")),
        "duration_s": parse_duration_s(e),
        "weight_lb": num(e.get("weight_lb")),
        "other_load": e.get("other_load") or None,
        "note": e.get("note") or None,
        "warmup": bool(e.get("warmup", False)),
        "actuals": e.get("actuals"),
    }


def norm_workout(w):
    status = str(w.get("status", "planned")).lower()
    if status not in STATUSES:
        raise ValueError(f"bad status {status!r} for {w.get('date')} {w.get('title')}")
    datetime.strptime(w["date"], "%Y-%m-%d")
    return {
        "date": w["date"],
        "title": str(w["title"]).strip(),
        "type": w.get("type", "Strength"),
        "status": status,
        "status_note": w.get("status_note") or None,
        "exercises": [norm_exercise(e) for e in w.get("exercises", [])],
    }


def key(w):
    return f"{w['date']}|{w['title']}"


def content(w):
    """The comparable part of a workout (excludes bookkeeping)."""
    return {k: w[k] for k in ("date", "title", "type", "status", "status_note", "exercises")}


def carry_actuals(old, new):
    """Keep actuals already recorded if the new batch doesn't supply them."""
    prev = {(e["label"], e["name"]): e.get("actuals") for e in old["exercises"]}
    for e in new["exercises"]:
        if e.get("actuals") is None and prev.get((e["label"], e["name"])) is not None:
            e["actuals"] = prev[(e["label"], e["name"])]


def load(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"schema": 1, "workouts": {}, "merges": []}


def save(path, store):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(store, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def merge(store, batch, source_name="batch", overrides=None):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    added = updated = unchanged = 0
    preserved = {}
    if overrides:
        for w in store.get("workouts", {}).values():
            sk = w.get("session_key")
            if sk and sk in overrides:
                preserved[sk] = copy.deepcopy(w.get("exercises"))
    src = batch.get("source", "TrainingPeaks")
    for raw in batch["workouts"]:
        new = norm_workout(raw)
        k = key(new)
        old = store["workouts"].get(k)
        if old is None:
            # Same workout already moved (via log.py --move) onto this date? Treat as the same workout
            # instead of adding a duplicate.
            twin = next((ow for ow in store["workouts"].values()
                         if ow.get("moved_to") == new["date"] and ow["title"] == new["title"]), None)
            if twin is not None:
                unchanged += 1
                continue
        if old is None:
            new.update(source=src, first_seen=now, last_updated=now, revisions=[])
            store["workouts"][k] = new
            added += 1
            continue
        carry_actuals(old, new)
        # Exercises logged via chat as extras aren't in TrainingPeaks; keep them.
        names = {(e["label"], e["name"]) for e in new["exercises"]}
        new["exercises"] += [e for e in old["exercises"] if e.get("extra") and (e["label"], e["name"]) not in names]
        # A batch that still says "planned" never un-does a recorded completed/skipped.
        if new["status"] == "planned" and old["status"] in ("completed", "skipped"):
            new["status"] = old["status"]
        # A batch with no note never erases a note already on file (e.g. User's moved/done note).
        if not new.get("status_note") and old.get("status_note"):
            new["status_note"] = old["status_note"]
        # User's own status call always wins over TrainingPeaks.
        if old.get("status_locked"):
            new["status"] = old["status"]
        # A dashboard-moved workout isn't auto-completed from TrainingPeaks; flag it instead.
        elif old.get("moved_to") and new["status"] != old["status"] and new["status"] != "planned":
            store.setdefault("status_flags", []).append(
                {"at": now, "workout": k, "tp_status": new["status"], "kept": old["status"]})
            new["status"] = old["status"]
        # TrainingPeaks completion date/time (used for Whoop pairing), only when it's really completed.
        for f in ("completed_date", "completed_time"):
            if new.get(f) and new["status"] == "completed":
                old[f] = new[f]
        if content(old) == content(new):
            unchanged += 1
            continue
        snapshot = copy.deepcopy(content(old))
        snapshot["replaced_at"] = now
        old.setdefault("revisions", []).append(snapshot)
        old.update(content(new))
        old["last_updated"] = now
        updated += 1
    if added or updated:
        store.setdefault("merges", []).append(
            {"at": now, "batch": source_name, "added": added, "updated": updated, "unchanged": unchanged})
    if overrides:
        hold_user_workout_overrides(store, overrides, preserved)
    store["workouts"] = dict(sorted(store["workouts"].items()))
    return added, updated, unchanged


def merge_actuals(store, export, source_name="actuals"):
    """Fold a dashboard actuals export (browser-logged sets) into the store.

    export = {"kind": "actuals_export", "export_id": .., "exported_at": ..,
              "workouts": {"DATE|Title": {"status": "completed"|None,
                  "exercises": {"LABEL|Name": {"sets": [{"weight_lb":165,"reps":10}, ...], "notes": ..}}}}}
    Legacy entries {"weight_lb": .., "reps": "10,10,8"} are also accepted.
    Logged sets are appended to existing actuals; an export is only ever imported once.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    exp_id = export.get("export_id") or hashlib.sha1(
        json.dumps(export.get("workouts", {}), sort_keys=True).encode()).hexdigest()
    done = store.setdefault("imported_exports", [])
    if exp_id in done:
        return 0, len(export.get("workouts", {})), []
    updated = unchanged = 0
    missing = []
    for wkey, entry in export.get("workouts", {}).items():
        w = store["workouts"].get(wkey)
        if w is None:
            missing.append(wkey)
            continue
        snapshot = copy.deepcopy(content(w))
        changed = False
        st = (entry.get("status") or "").lower()
        if st in STATUSES and st != w["status"]:
            w["status"] = st
            changed = True
        for ekey, act in entry.get("exercises", {}).items():
            label, _, name = ekey.partition("|")
            ex = next((e for e in w["exercises"] if e["label"] == label and e["name"] == name), None)
            if ex is None:
                missing.append(f"{wkey} / {ekey}")
                continue
            if act.get("sets"):
                new_sets = [{k: v for k, v in s_.items() if v is not None} for s_ in act["sets"]]
            else:
                wt, reps = _num(act.get("weight_lb")), _reps(act.get("reps"))
                if reps is None:
                    new_sets = [{"weight_lb": wt}] if wt is not None else []
                else:
                    reps = reps if isinstance(reps, list) else [reps] * (ex.get("sets") or 1)
                    new_sets = [{k: v for k, v in {"weight_lb": wt, "reps": r}.items() if v is not None} for r in reps]
            notes = (act.get("notes") or "").strip() or None
            if not new_sets and not notes:
                continue
            cur = {"sets": list(actual_sets(ex)), "notes": (ex.get("actuals") or {}).get("notes")}
            cur["sets"] += new_sets
            if notes:
                cur["notes"] = notes if not cur["notes"] else f"{cur['notes']}; {notes}"
            cur["logged_at"] = export.get("exported_at") or now
            ex["actuals"] = cur
            fill_per_plan(ex)
            changed = True
        if changed:
            snapshot["replaced_at"] = now
            w.setdefault("revisions", []).append(snapshot)
            w["last_updated"] = now
            updated += 1
        else:
            unchanged += 1
    for wkey, to in (export.get("moves") or {}).items():
        w = store["workouts"].get(wkey)
        if w is None:
            missing.append(f"move {wkey}")
            continue
        target = None if (not to or to == w["date"]) else to
        if w.get("moved_to") != target:
            w.setdefault("move_history", []).append({"at": now, "from": eff_date(w), "to": target or w["date"], "via": "dashboard export"})
            w["moved_to"] = target
            w["last_updated"] = now
            updated += 1
    done.append(exp_id)
    store.setdefault("merges", []).append(
        {"at": now, "batch": source_name, "kind": "actuals", "updated": updated, "unchanged": unchanged})
    return updated, unchanged, missing


def _num(v):
    if v is None or str(v).strip() == "":
        return None
    try:
        f = float(v)
    except ValueError:
        return None
    return int(f) if f.is_integer() else f


def _reps(v):
    """Reps may be a single number or per-set list like "10,10,8"."""
    if v is None or str(v).strip() == "":
        return None
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, list):
        return [_num(x) for x in v if _num(x) is not None] or None
    parts = [p for p in str(v).replace("/", ",").replace(" ", ",").split(",") if p.strip()]
    nums = [_num(p) for p in parts]
    nums = [n for n in nums if n is not None]
    if not nums:
        return None
    return nums[0] if len(nums) == 1 else nums


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch")
    ap.add_argument("--store", default=DEFAULT_STORE)
    a = ap.parse_args()
    with open(a.batch) as f:
        batch = json.load(f)
    if isinstance(batch, list):
        batch = {"workouts": batch}
    store = load(a.store)
    before = len(store["workouts"])
    if batch.get("kind") == "actuals_export":
        updated, unchanged, missing = merge_actuals(store, batch, os.path.basename(a.batch))
        save(a.store, store)
        print(f"merged actuals {os.path.basename(a.batch)}: {updated} workouts updated, {unchanged} unchanged")
        for m in missing:
            print(f"  warning: not in store, skipped: {m}")
        return
    added, updated, unchanged = merge(store, batch, os.path.basename(a.batch),
                                      overrides=load_user_overrides(os.path.join(ROOT, "data", "user_overrides.json")) or None)
    assert len(store["workouts"]) >= before, "merge must never delete workouts"
    save(a.store, store)
    print(f"merged {os.path.basename(a.batch)}: {added} added, {updated} updated, "
          f"{unchanged} unchanged; store now has {len(store['workouts'])} workouts")


if __name__ == "__main__":
    sys.exit(main())
