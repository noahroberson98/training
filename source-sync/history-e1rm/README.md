# History progression and estimated 1RM

Follow-up to the unmerged repair. This directory is the generator handoff. It does not replace `index.html` and it is not a release.

Apply it on the local training-dashboard after the approved run8 generator patches. The GitHub training repository only publishes generated HTML. A daily rebuild from an unpatched template would drop this History chart.

Noah approved publication of run8 and of History after review on Nov 6, 2026. This branch was not merged and nothing was deployed.

## What the chart does

On History, each exercise can show a mobile-width chart of dated sessions:

- top set: heaviest logged weight, then more reps
- estimated one-rep max: Epley, `weight * (1 + reps / 30)`, for 2 or more reps
- Brzycki, `weight * 36 / (37 - reps)`, only as a labeled comparison for 2–10 reps
- a logged 1-rep set stays at that weight and is not inflated by Epley
- reps above 12 stay on the chart but are marked low confidence and are not joined to the solid estimate line

Only finite, positive, whole-rep loads are used. Plan-filled reps, round taps, warm-ups, assisted loads, zeros, and missing numbers are left out. See `DATA_PROVENANCE.md` and `FORMULAS.md`.

## Dependency

- Repair branch `cursor/pt-upper-one-session-c4c3` at `7d00bb7417ada9aecb4523dd0189b91068c8d8fd` (run12), merged into this History branch
- Run8 package SHA256, still the earlier template base: `85814fb15404ba2db14cc0b4ada91339296e86a344c2ff784149342fa4c742d8`
- Updated repair template SHA256, the History patch preimage: `d5946907beb0dbaff8b1d20a8b7d5c33710423270ac0e9ee9af6aa384529a7f5`
- History template SHA256: `5ad77b37042ab419d10c0823915e6376a7277276e9210b7e2db212a7f29fc555`
- `build.py` baseline `1506ec0b0ebefedcbad5200581cacc5858f8d6ac16c6a682465deec6e2f90034` is unchanged

Run12 adds known-load volume with a missing-load count, and shows “Pounds assumed” only when the stored unit note says the pounds were assumed. Incline weight is not doubled. The History patch keeps those behaviors.

`APPLY.md` is the apply order. Do not reset the local generator. Its git repo has no remote, and several dirty files were not in the source kit.
