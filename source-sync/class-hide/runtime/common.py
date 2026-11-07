"""Shared helpers: set parsing/formatting, best-set ranking, exercise-name matching."""
import difflib, json, os, re

# ---------- sets ----------
_NUM = r"(\d+(?:\.\d+)?)"


def _n(v):
    f = float(v)
    return int(f) if f.is_integer() else round(f, 1)


def parse_duration(tok):
    t = tok.strip().lower()
    m = re.fullmatch(r"(\d+):(\d{1,2})", t)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.fullmatch(_NUM + r"\s*(s|sec|secs|seconds?)", t)
    if m:
        return _n(m.group(1))
    m = re.fullmatch(_NUM + r"\s*(min|mins|minutes?)", t)
    if m:
        return _n(float(m.group(1)) * 60)
    return None


def _weight(tok):
    t = tok.strip().lower().replace(" ", "")
    if t in ("bw", "bodyweight", "body"):
        return None, True
    m = re.fullmatch(_NUM + r"(lb|lbs|#)?", t)
    if m:
        return _n(m.group(1)), True
    m = re.fullmatch(_NUM + r"kg", t)
    if m:
        return _n(round(float(m.group(1)) * 2.20462 * 2) / 2), True
    return None, False


def parse_sets(text):
    """Parse '165x10,165x10,165x8' style input into a list of set dicts.

    Supported per comma-separated token:
      165x10 / 165×10 / 165lb x 10 / 75kg x 8   weight x reps
      165x10x3                                  weight x reps x sets
      3x10@165                                  sets x reps @ weight
      bw x 12 / 12                              reps only
      30s / 1:30 / 5min                         timed
      6lb x 30s / 110x10m                       weight + time / distance
    """
    out = []
    for raw in re.split(r"[,;]", text):
        tok = raw.strip().lower().replace("×", "x").replace("*", "x")
        if not tok:
            continue
        tok = re.sub(r"\s*x\s*", "x", tok)
        tok = re.sub(r"\s*@\s*", "@", tok)
        m = re.fullmatch(r"(\d+)x(\d+)@(.+)", tok)  # 3x10@165
        if m:
            w, ok = _weight(m.group(3))
            if not ok:
                raise ValueError(f"can't read weight in {raw!r}")
            out += [_clean({"weight_lb": w, "reps": int(m.group(2))}) for _ in range(int(m.group(1)))]
            continue
        d = parse_duration(tok)
        if d is not None:
            out.append({"duration_s": d})
            continue
        if re.fullmatch(r"\d+", tok):
            out.append({"reps": int(tok)})
            continue
        parts = tok.split("x")
        if len(parts) in (2, 3):
            w, ok = _weight(parts[0])
            if not ok:
                raise ValueError(f"can't read weight in {raw!r}")
            second = parts[1]
            s = {"weight_lb": w}
            dd = parse_duration(second)
            dm = re.fullmatch(_NUM + r"m", second)
            if dd is not None:
                s["duration_s"] = dd
            elif dm:
                s["distance_m"] = _n(dm.group(1))
            elif re.fullmatch(r"\d+", second):
                s["reps"] = int(second)
            else:
                raise ValueError(f"can't read reps/time in {raw!r}")
            n = int(parts[2]) if len(parts) == 3 and parts[2].isdigit() else 1
            out += [_clean(dict(s)) for _ in range(n)]
            continue
        raise ValueError(f"can't parse set {raw!r} (try 165x10, 10, 30s)")
    if not out:
        raise ValueError("no sets given")
    return out


def _clean(s):
    return {k: v for k, v in s.items() if v is not None}


def fmt_dur(s):
    if s is None:
        return ""
    s = int(s)
    return f"{s // 60}:{s % 60:02d}" if s >= 60 else f"{s}s"


def set_label(s):
    w, r, d, m = s.get("weight_lb"), s.get("reps"), s.get("duration_s"), s.get("distance_m")
    if w is not None and r is not None:
        return f"{w:g}×{r}"
    bits = []
    if w is not None:
        bits.append(f"{w:g} lb")
    if r is not None:
        bits.append(str(r))
    if d is not None:
        bits.append(fmt_dur(d))
    if m is not None:
        bits.append(f"{m:g}m")
    return " · ".join(bits) or "?"


def actual_sets(ex):
    """Normalised logged sets for an exercise (supports legacy weight_lb/reps actuals)."""
    a = ex.get("actuals") or {}
    if a.get("sets"):
        return a["sets"]
    if a.get("weight_lb") is None and a.get("reps") is None:
        return []
    reps = a.get("reps")
    if not isinstance(reps, list):
        reps = [reps] * (ex.get("sets") or 1)
    return [_clean({"weight_lb": a.get("weight_lb"), "reps": r}) for r in reps]


def set_rank(s):
    """Sortable key: weighted reps (Epley e1RM) > weight×distance/time > time > reps."""
    w, r, d = s.get("weight_lb"), s.get("reps"), s.get("duration_s")
    if w is not None and r is not None:
        return (3, w * (1 + r / 30.0), w)
    if w is not None:
        return (2, w, d or s.get("distance_m") or 0)
    if d is not None:
        return (1, d, 0)
    return (0, r or 0, 0)


def best_set(sets):
    return max(sets, key=set_rank) if sets else None


def volume(sets):
    return sum((s.get("weight_lb") or 0) * (s.get("reps") or 0) for s in sets)


# ---------- name matching ----------
_SYN = [(r"\bdumb ?bells?\b", "db"), (r"\btriceps\b", "tricep"), (r"\bbiceps\b", "bicep"),
        (r"\bpulldowns?\b", "pull down"), (r"\bpushdowns?\b", "push down"), (r"\bpushups?\b", "push up"),
        (r"\bsitups?\b", "sit up"), (r"\bromanian deadlifts?\b", "rdl"), (r"\bkettlebells?\b", "kb"),
        (r"\bbarbell\b", "bb"), (r"\bmedicine\b", "med"), (r"\bmedball\b", "med ball"), (r"\bsquats\b", "squat"),
        (r"\braises\b", "raise"), (r"\bcurls\b", "curl"), (r"\brows\b", "row"), (r"\bjumps\b", "jump"),
        (r"\bflyes\b|\bflies\b", "fly")]


def norm_name(s):
    s = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    for pat, rep in _SYN:
        s = re.sub(pat, rep, s)
    toks = [t[:-1] if len(t) >= 3 and t.endswith("s") and not t.endswith("ss") else t for t in s.split()]
    return " ".join(toks)


def match_score(query, name):
    q, n = norm_name(query), norm_name(name)
    if not q or not n:
        return 0.0
    if q == n:
        return 1.0
    qt, nt = q.split(), n.split()
    ratio = difflib.SequenceMatcher(None, q, n).ratio()
    if all(t in nt for t in qt):
        return 0.9 + 0.05 * len(qt) / len(nt)
    if all(t in qt for t in nt):
        return 0.85
    if q in n or n in q:
        return 0.8
    # token-level fuzzy overlap (handles small typos)
    hits = sum(1 for t in qt if any(difflib.SequenceMatcher(None, t, u).ratio() >= 0.8 for u in nt))
    return 0.6 * hits / max(len(qt), len(nt)) + 0.4 * ratio


def eff_date(w):
    """Date the workout is actually scheduled on (dashboard move override, else TrainingPeaks date)."""
    return w.get("moved_to") or w["date"]


# ---------- User rule 10/21: weight logged but no reps = prescribed reps ----------
def fill_per_plan(ex):
    """Fill reps on weighted sets that have no reps from the prescription; mark them per_plan.
    Returns the number of sets filled. Never touches sets that already have reps."""
    a = ex.get("actuals") or {}
    rx = ex.get("reps")
    if not a.get("sets") or not rx or ex.get("warmup"):
        return 0
    n = 0
    for s in a["sets"]:
        if s.get("weight_lb") is not None and s.get("reps") is None and s.get("duration_s") is None:
            s["reps"] = rx
            s["per_plan"] = True
            n += 1
    return n


def fill_store_per_plan(store):
    return sum(fill_per_plan(e) for w in store["workouts"].values() for e in w["exercises"])


def session_key(date, time, name):
    return f"{date}|{time}|{name}"


def load_user_overrides(path):
    """Read the prospective user_overrides.json. Missing file means no overrides."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    out = {}
    for key, row in (doc.get("sessions") or {}).items():
        if isinstance(row, dict):
            out[row.get("session_key") or key] = row
    return out


def apply_user_class_override(entry, ov):
    """A user hide/cancel is not a provider cancellation and does not refresh the feed clock.

    Undo (hidden false) changes visibility only. csv_status and source stay as the feed left them.
    """
    if not entry or not ov:
        return entry
    verified = bool(ov.get("provider_cancellation_verified"))
    user_status = str(ov.get("status") or "").lower()
    hidden = ov.get("hidden")
    entry["provider_cancellation_verified"] = verified
    entry["user_override"] = {
        "status": ov.get("status"),
        "attendance": ov.get("attendance"),
        "hidden": hidden,
        "provider_cancellation_verified": verified,
        "source": ov.get("source") or "user",
        "reported_at": ov.get("reported_at"),
    }
    if user_status == "cancelled" and not verified:
        entry["status"] = "CANCELLED"
        entry["cancel_source"] = "user"
        entry["hidden"] = True if hidden is None else bool(hidden)
    elif hidden is False:
        entry["hidden"] = False
    elif hidden is True:
        entry["hidden"] = True
    return entry


def hold_user_workout_overrides(store, overrides, preserved_exercises=None):
    """Do not let a feed rewrite complete or drop a user-cancelled session's logged sets.

    status_locked still wins. Hidden false only clears the hide flag.
    preserved_exercises is the pre-merge exercise list keyed by session_key.
    """
    if not overrides:
        return
    preserved_exercises = preserved_exercises or {}
    for w in store.get("workouts", {}).values():
        sk = w.get("session_key") or ""
        ov = overrides.get(sk)
        if not ov:
            continue
        if sk in preserved_exercises and preserved_exercises[sk] is not None:
            w["exercises"] = preserved_exercises[sk]
        if w.get("status_locked"):
            if ov.get("hidden") is not None:
                w["user_hidden"] = bool(ov.get("hidden"))
            continue
        if str(ov.get("status") or "").lower() == "cancelled" and not ov.get("provider_cancellation_verified"):
            if w.get("status") == "completed" or str(ov.get("attendance") or "").lower() == "skipped":
                w["status"] = "skipped"
            w["user_cancel_source"] = "user"
            w["provider_cancellation_verified"] = False
        if ov.get("hidden") is False:
            w["user_hidden"] = False
        elif ov.get("hidden"):
            w["user_hidden"] = True
