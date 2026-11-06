# Tests run for this handoff

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
