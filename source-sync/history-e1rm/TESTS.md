# Persistence status

`test_e1rm_persist.py` expects an honest unsaved state when `localStorage.setItem` throws. On the unchanged safe page `42b5a430…` that test exits 1. The summary still says “Saved on this phone only.” There is no retry control. Quota and blocked-storage writes stay in memory and do not land in storage. The same test on the corrected review page exits 0: the failure is visible, retry persists the in-memory sent mark without another send, a reload does not send by itself, and Done after a failed persist can send again because the mark was not durable. Local 500, local 200, a thrown request, and the 12 second abort do not mark sent when delivery fails. Playwright logs `CancelledError` from the route callback when the page aborts the hanging request. The assertions still pass.

The quick-log button, the typed set row, and the existing `data-addset` prompt handler were exercised on `2026-10-23|Upper Body`, not on the Nov 6 six-set workout. No rendered button uses `data-addset`; the test adds one so that handler runs. `+ Add Set` on screen is `data-addrow`. `saveMoves` and `saveFree` still swallow their own storage errors. Summary `completed_at` changes. The recorded Nov 6 start and end do not.

# Test assumptions corrected after the fresh build

Initial failures, unchanged product page:

- `test_e1rm_history.py` failed one check, "generator token line was not rewritten", because it required `const FS_TOKEN="REDACTED_FORMSUBMIT_ALIAS"`. A production template correctly keeps its real token. The check now requires one assignment, a History patch that does not mention `FS_TOKEN`, and a sentinel token that the preview builder must clear. Leaving that sentinel in place fails a negative control. The token value is not printed.
- `test_e1rm_current.py` failed "menu uses the snapshot's own build clock" because it required `Nov 6, 2026 6:27 PM CT` and the phrase `historical preview`. The fresh safe page's own line is `Nov 6, 2026 7:03 PM CT` and does not add that phrase. The test also rebuilt a temporary preview, so it was not a test of the exact file. It now runs `test_e1rm_exact.py` on the given file, hashes it before and after, and reads the build clock from that file. Replacing the clock with `current-data-preview` or another time fails a negative control.

These were fixture assumptions, not product defects. The attached safe HTML was not edited.

# Tests after the Style corrections

H1–H4 and S1–S2 are covered by `test_e1rm_history.py` and `test_e1rm_exact.py`, including an escaped `<img>` / `&` / quote canary in a point tooltip, a logged single with no Brzycki value, and a mixed-unit caption that does not claim every table row is on the chart. The exact-page test reads the build clock from the file it is given. On the fresh safe page that clock is `Nov 6, 2026 7:03 PM CT`, with no historical-preview tag. The earlier `6:27 PM CT` line belonged to the historical snapshot only. The exact-page test also checks the six `t240u#` ids and that the dormant cancellation-relay block is absent. The relay source block in the template still matches the run12 template byte for byte.

# Tests run after the run12 merge

`python3 tests/test_e1rm_history.py` passed, including the check that a High Incline Press load is not doubled and that assumed pounds stay on the pound series at the stored weight.

`python3 tests/test_e1rm_current.py` passed against the sanitized current snapshot. STORE and EXTRA matched byte for byte. The page token was empty. Machine Row showed Oct 30 and Nov 6, with “Pounds assumed”. Nov 6 still had six logged actual sets on Machine Row and High Incline Press. AbMat Sit Up had no estimate. Opening History did not write the log or the clock. HTTP was aborted. No page errors.

`tests/test_pt_session.py` was run on the run12 `index.html` and a local empty-finish draft of that same repair payload. Exit 0, `ALL PASSED`. Playwright again logged `asyncio.exceptions.CancelledError` from a route callback during the hanging finish. The timeout checks passed. The test file was not edited.

`tests/test_logging.py` and `tests/test_counting.py` were passed that run12 page and exited 0. `tests/test_nan_pills.py` and `tests/test_fontsize.py` passed when that page was placed at the `dashboard.html` path they hard-code. The copy was deleted afterward. No portable run12 recipe beyond these existing tests was in the repository.

No CI check has run. A local pass is not a CI pass. Style has not cleared a current-input production build. This was not a live JARVIS review.

`python3 tests/test_e1rm_history.py` passed after the final template edit. It checks the formulas, 1-rep handling, rep limits, warm-ups, plan fills, missing and non-finite loads, kilogram versus pound series, dumbbell loads that are not doubled, assisted loads, stable-id dedupe, repeated sets without an id, same-day sessions, the example chart, the empty state, and that picking an exercise does not write `localStorage` or call the network.

The run8 browser file `tests/test_pt_session.py` was run against a local candidate and a local empty-finish draft. Exit 0, `ALL PASSED`. It still shows one Upper Body session, 0 logged and 27 planned on the untouched Nov 6 payload, Log sets after an empty finish, the recorded 11:33 window through reload, summary, and a second summary, a live clock on a workout that has no recorded finish, and `fs_sent` only after HTTP 200. Copy does not mark sent. A hanging finish still leaves `fs_sent` unset after the 12 second abort.

`tests/test_logging.py` and `tests/test_counting.py` were passed the same candidate. Exit 0. `tests/test_nan_pills.py` and `tests/test_fontsize.py` passed when the candidate was placed at the `dashboard.html` path those files hard-code. `tests/test_class_history.py` and `tests/test_whoop_pair.py` passed.

## First failures, then what happened

- `test_e1rm_history.py` once compared a 110×3 Epley result with `== 121`. JavaScript produces `121.00000000000001`. The assertion now uses a tolerance. The formula did not change.
- `test_nan_pills.py` first failed with `ERR_FILE_NOT_FOUND` for `dashboard.html`. Re-run against the local candidate passed. The test file was not edited.
- Playwright's Python package was not installed in this environment. `pip install --user playwright` was used so the existing tests could launch the system Chrome at `/usr/bin/google-chrome`. No project dependency file was added.
- While `test_pt_session.py` was still on its hanging-route timeout check, Playwright logged `asyncio.exceptions.CancelledError` from a route callback. The timeout assertions passed, and the process exited 0. That is a harness teardown exception, not a failed check.

## Not run to a pass, because the current kit does not include those files

These failed on import or a missing path. They were not rewritten, and the missing personal store was not recreated.

- `test_history.py` — `review_email` is not in the kit
- `test_free_workout.py` — `ingest_logs` is not in the kit
- `test_drag.py`, `test_sync.py`, `test_skip.py` — `data/workouts.json` is not in the kit
- `test_backfill_guard.py` — the pre-ingest backup is not in the kit
- `test_cancel.py` — `ingest_cancel` is not in the kit
- `test_review_guard.py` — `review_guard` is not in the kit

The current kit's dirty-file list also names `scripts/merge.py`, `scripts/review_analysis.py`, `scripts/review_queue.py`, and the data JSON files. This patch does not touch them. No parity is claimed for them.

No GitHub check ran on this branch. A local pass is not a CI pass. Total Fitness style review, JARVIS embed review, and a current-data production build were not done.
