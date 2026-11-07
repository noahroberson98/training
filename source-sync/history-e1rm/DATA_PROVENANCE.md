# What counts as a logged set

The chart reads sets that are already on the page. It does not rewrite the store, browser log, clock, or plan.

The published page's embedded store, inspected for field names only, has this shape. Eight workouts. Exercise fields are `label`, `block`, `name`, `sets`, `reps`, `duration_s`, `weight_lb`, `other_load`, `note`, `warmup`, `actuals`. Actuals fields seen: `sets`, `sync_notes`, `logged_at`, `notes`, `skipped_sets`. Set fields seen: `weight_lb`, `reps`, `duration_s`, `distance_m`, `per_plan`, `round`, `override`, `src`. There is no `unit`, `weight_kg`, `basis`, `per_hand`, or set id in that store. Browser logs can carry `id`, `set_id`, or `eid`. The generator's entry parser converts a typed kilogram load into `weight_lb` before it is stored. A set that still has only `weight_kg` is kept in kilograms and is not converted again here.

## Included

A set is eligible when all of these hold:

- the exercise is not marked `warmup`, and the set is not marked `warmup`
- `per_plan`, `round`, `planned`, and `from_plan` are not true, and `src` is not `"plan"`
- the exercise name is not an assisted lift, and the set is not marked assistance
- weight is a finite number greater than 0, in `weight_lb` or, if that is absent, `weight_kg`
- reps are a finite whole number of at least 1
- if both `weight_lb` and `weight_kg` are present, they agree within 2% of `kg * 2.20462`; otherwise the set is a unit conflict and is dropped

`override` without `per_plan` is a confirmed logged weight. It is included when the reps are real. `src: "sync"` is not, by itself, a plan fill.

If the flags above are absent and the weight and reps are real, the set is treated as logged. The plan-fill path sets `per_plan` or `round`. A hand edit that omitted those flags cannot be told apart from a typed set. That ambiguity is left as ambiguity. Equality with the planned weight is not treated as a fill.

## Excluded

- exercise or set warm-ups. Warm-up is a flag on the exercise in this store. There is no reliable set-level warm-up flag on working exercises, so the first working set is not guessed to be a warm-up.
- plan-filled reps (`per_plan`) and round taps that copy the plan
- zero, negative, NaN, Infinity, missing weight, missing reps, and fractional reps
- assisted names and assistance loads. The stored number is not the weight lifted, and body weight is not in the log, so no total is invented
- bodyweight exercises with reps and no external load. No body weight is invented
- distance or duration without a whole rep count

Dumbbell and kettlebell names (`dumbbell`, `kettlebell`, `db`, `kb`) keep the stored number. The log does not say per hand or total, so the chart does not double it and labels that limit. Those points are not placed on a barbell series.

Kilograms and pounds are separate series. A change is shown only against the previous session in the same unit and basis. One session says there is nothing earlier to compare. No eligible set says there is no estimate, including when logged sets exist but were excluded, and it says why they were excluded.

`actuals.unit_note` is provenance text. When it matches the repair rule (`assum` or `omit`), the exercise is labeled “Pounds assumed”. The stored `weight_lb` is still the number used. It is not converted and not doubled. A note that says an incline load was stored as written does not multiply that load. Week volume still uses the repair’s known-load count: a logged set adds to volume only when weight and reps are both finite, and the week line says how many logged sets have no recorded load.

## Identity

Sessions stay on the workout key (`date` plus title). Two workouts on the same date are two points. Exercise identity is the existing normalized name. Different implements are not fuzzy-merged. Notes stay notes. They are not parsed into weight.

Within one session, a repeated `id`, `set_id`, or `eid` is kept once, the first copy. The same weight and reps with no id are kept. That matches the run8 rule that equal weight and reps are not the same set.

Opening History, picking an exercise, or searching does not call the save or sync writers. The exercise control updates the address bar with `history.replaceState` only.
