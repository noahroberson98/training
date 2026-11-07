"""Pair Whoop activities with completed TrainingPeaks workouts and THIS Gym classes.

Rules (see README):
 1. Same day only: the date the item was actually done (completed_date > dashboard move > plan date).
 2. Hard vetoes: start times >90 min apart (unless the session overlaps the item), or a known
    activity type that clearly doesn't fit (e.g. Running vs a strength workout).
 3. Score: time proximity (<=15 min +3, <=45 min +2, overlap +2) + activity type fits (+2)
    + Whoop's own source label fits (+1) + fuzzy name overlap (+0.5, tiebreaker only).
 4. Pair only at score >= 2 and when the best session beats the runner-up for that item
    (a tie = ambiguous = unpaired). Each Whoop session is used once: best-scoring pairs win first.
Files are read-only and re-read on every build."""
import csv, os, re

STRENGTH = {"weightlifting", "functional fitness", "strength trainer", "powerlifting", "crossfit",
            "hiit", "training", "box fitness", "bodybuilding", "other"}
MIND_BODY = {"yoga", "pilates", "barre", "stretching", "hot yoga"}
CARDIO = {"running", "cycling", "spin", "rowing", "walking", "hiking", "swimming", "elliptical", "stairmaster"}
TYPES = sorted(STRENGTH | MIND_BODY | CARDIO, key=len, reverse=True)


def _rows(path):
    if not path or not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{k.strip().lower(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]


def mins(t):
    m = re.match(r"^(\d{1,2}):(\d{2})", t or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def _dur_min(d):
    m = re.match(r"^(?:(\d+):)?(\d{1,2}):(\d{2})$", d or "")
    if not m:
        return None
    return int(m.group(1) or 0) * 60 + int(m.group(2)) + int(m.group(3)) / 60 if m.group(1) else int(m.group(2)) + int(m.group(3)) / 60


def _first(r, *cols):
    for c in cols:
        if r.get(c):
            return r[c]
    return ""


def parse_notes(notes):
    out = {}
    low = notes.lower()
    for t in TYPES:
        if re.search(r"\b" + re.escape(t) + r"\b", low):
            out["activity"] = t.title(); break
    for key, rx in (("duration", r"\b(\d{1,2}:\d{2}:\d{2})\b"), ("avg_hr", r"avg(?:\.|erage)? ?hr:? ?(\d{2,3})"),
                    ("max_hr", r"max(?:imum)? ?(?:hr:? ?)?(\d{2,3})"), ("cal", r"(\d{2,5}) ?(?:k?cal|calories)\b"),
                    ("start", r"(?:start(?:ed)?|at) (\d{1,2}:\d{2})")):
        m = re.search(rx, notes, re.I)
        if m:
            out[key] = m.group(1)
    return out


def load_sessions(sessions_csv, daily_csv=None):
    """Whoop activities with real measurements. Planned/empty rows are ignored."""
    out = []
    for i, r in enumerate(_rows(sessions_csv)):
        n = parse_notes(r.get("notes", ""))
        s = {"id": f"sessions:{i + 2}", "date": r.get("date", ""), "session": r.get("session", ""),
             "source": r.get("source", ""),
             "time": _first(r, "start_time", "start", "actual_time") or n.get("start") or r.get("planned_time", ""),
             "time_kind": "actual" if (_first(r, "start_time", "start", "actual_time") or n.get("start")) else "planned",
             "activity": _first(r, "activity", "sport", "type") or n.get("activity", ""),
             "strain": _first(r, "whoop_workout_strain", "workout_strain", "strain"),
             "duration": _first(r, "duration") or n.get("duration", ""),
             "avg_hr": _first(r, "avg_hr", "average_hr") or n.get("avg_hr", ""),
             "max_hr": _first(r, "max_hr") or n.get("max_hr", ""),
             "cal": _first(r, "calories", "cal", "kcal") or n.get("cal", "")}
        if s["date"] and (s["strain"] or s["duration"]):
            out.append({k: v for k, v in s.items() if v != ""})
    have = {(s["date"], s.get("strain")) for s in out}
    for r in _rows(daily_csv):
        for j, w in enumerate(x.strip() for x in (r.get("workouts") or "").split(";") if x.strip()):
            st = re.search(r"strain (\d+(?:\.\d+)?)", w)
            if not st or (r.get("date"), st.group(1)) in have:
                continue
            n = parse_notes(w)
            s = {"id": f"daily:{r['date']}:{j}", "date": r["date"], "strain": st.group(1), **n}
            if n.get("start"):
                s["time"], s["time_kind"] = n["start"], "actual"
            out.append(s)
    return out


def _kind_fit(item, act):
    """+1 fits, 0 unknown, -1 clearly wrong."""
    if not act:
        return 0
    a = act.lower()
    name = (item.get("name", "") + " " + item.get("type", "")).lower()
    want = MIND_BODY if re.search(r"yoga|pilates|reformer|barre|sculpt|stretch", name) else STRENGTH
    if item["kind"] == "class" and re.search(r"conditioning|hyrox|apex|run|row", name):
        want = STRENGTH | {"running", "rowing", "cycling", "spin"}
    if a in want:
        return 1
    return -1 if a in (STRENGTH | MIND_BODY | CARDIO) else 0


def _tokens(s):
    return {t for t in re.findall(r"[a-z]+", (s or "").lower()) if len(t) > 2 and t not in {"this", "the", "body"}}


def score(item, s):
    """(score, [reasons]) or (None, reason) when vetoed."""
    if s["date"] != item["date"]:
        return None, "different day"
    pts, why = 0.0, []
    it, st = mins(item.get("time")), mins(s.get("time"))
    if it is not None and st is not None:
        d = abs(st - it)
        dur = _dur_min(s.get("duration"))
        overlap = dur is not None and st <= it <= st + dur
        if d > 90 and not overlap:
            return None, f"starts {d} min apart"
        if d <= 15:
            pts += 3; why.append(f"{s.get('time_kind', 'planned')} time {s['time']} within {d} min")
        elif d <= 45 or overlap:
            pts += 2; why.append(f"time {s['time']} {'overlaps' if overlap else f'within {d} min'}")
    kf = _kind_fit(item, s.get("activity"))
    if kf < 0:
        return None, f"activity {s['activity']} doesn't fit"
    if kf > 0:
        pts += 2; why.append(f"activity {s['activity']} fits {item['kind']}")
    src = (s.get("source") or "").lower()
    if src and ((item["kind"] == "class" and "gym" in src) or (item["kind"] == "workout" and "trainingpeaks" in src)):
        pts += 1; why.append(f"Whoop label '{s['source']}'")
    if _tokens(item.get("name")) & _tokens(s.get("session")) or (item.get("name", "").lower() == (s.get("session") or "").lower() != ""):
        pts += 0.5; why.append("name similar")
    return pts, why


def pair(items, sessions, min_score=2.0):
    """items: [{id,date,time?,kind:'class'|'workout',name,type?}] -> {item_id: (session, match)}"""
    cand = []
    best_per_item = {}
    for it in items:
        scored = []
        for s in sessions:
            p, why = score(it, s)
            if p is not None and p >= min_score:
                scored.append((p, s, why))
        scored.sort(key=lambda x: -x[0])
        # ambiguous if the top two candidates tie
        if len(scored) > 1 and scored[0][0] == scored[1][0]:
            best_per_item[it["id"]] = "ambiguous"
        cand += [(p, it, s, why) for p, s, why in scored]
    cand.sort(key=lambda x: -x[0])
    used_s, out = set(), {}
    for p, it, s, why in cand:
        if it["id"] in out or s["id"] in used_s:
            continue
        # top-tie ambiguity only matters if the tied rival is still available
        if best_per_item.get(it["id"]) == "ambiguous":
            rivals = [c for c in cand if c[1]["id"] == it["id"] and c[0] == p and c[2]["id"] not in used_s]
            if len(rivals) > 1:
                continue
        conf = "high" if p >= 4 else ("medium" if p >= 3 else "low")
        out[it["id"]] = (s, {"confidence": conf, "score": p, "reason": "; ".join(why), "whoop_id": s["id"]})
        used_s.add(s["id"])
    return out
