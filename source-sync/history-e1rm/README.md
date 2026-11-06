# History progression and estimated 1RM

Follow-up to the unmerged run8 repair. This directory is the generator handoff. It does not replace `index.html` and it is not a release.

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

- Run8 head: `b59aa2b2b9774388efa3cb84b257beb64f274296` on `cursor/pt-upper-one-session-c4c3`
- Run8 package SHA256: `85814fb15404ba2db14cc0b4ada91339296e86a344c2ff784149342fa4c742d8`
- Current source kit SHA256: `4884a5a41e693ac51d4ce7c768e23319ca031d09a8d54cf9ece972ecb861e8b6`
- Template baseline before this patch, after run8: raw historical `9a3927c79c8621d8380b05b0f5a1b48909d4d7e2baf32311a1618f7ea2f9194f`, patched template `e3a379d4a9dcf7c1b54b8a29096db52abb6840ca3171a89d11d2e6560c7913dd`
- `build.py` baseline `1506ec0b0ebefedcbad5200581cacc5858f8d6ac16c6a682465deec6e2f90034` is unchanged

`APPLY.md` is the apply order. Do not reset the local generator. Its git repo has no remote, and several dirty files were not in the source kit.
