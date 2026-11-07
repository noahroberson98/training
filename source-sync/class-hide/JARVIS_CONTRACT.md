# JARVIS owner contract

Do not publish this branch. Do not apply the held training-overview bookings change. Do not change the morning or afternoon routines. Do not restore the emptied credential. Do not send mail.

## What JARVIS may store

One JSON object, `data/user_overrides.json`, schema 1. Each session key is `date|time|class`.

Fields that matter:

- `status`: `cancelled` when the person reported it. This is not a gym confirmation.
- `attendance`: `skipped` when they did not go.
- `hidden`: true after Hide, false after Undo.
- `provider_cancellation_verified`: false unless a provider confirmation exists. This patch never sets it true.
- `source`, `reported_at`: the user report. Do not copy these over the feed `source` string.

Undo changes `hidden` only. It must leave the cancellation note, the logged sets, and the feed `csv_status` alone.

## What the feed may overwrite

`thisgym_reservations.csv` and `thisgym_schedule.json` are rewritten by the browser routines from PushPress. Those files are not the override store. A later reserved row, or a missing row, must not bring a hidden session back as a normal booking when `user_overrides.json` still hides it. `build.py` and `merge.py` are the readers. The routines themselves are not edited here and were not verified.

## What the code does

`scripts/build.py` reads `data/user_overrides.json` while updating `data/class_history.json`.

- A reserved feed row with a user cancellation stays `csv_status` `RESERVED`, display status `CANCELLED`, `cancel_source` `user`, and `hidden` as stored.
- A row missing from the feed is not marked completed when that override exists.
- No class record is created merely because an override exists and the history has no row.

`scripts/merge.py` reads the same file while updating `data/workouts.json`.

- A workout with `session_key` set to that session is not left completed by the feed.
- Its exercises and logged sets are kept.
- `status_locked` is not cleared and its status is not replaced.

`scripts/sync_guard.py` and `scripts/lock_status.py` are unchanged.

`scripts/template.html` is the page. Day cards and week cards both get Hide. Hidden By You has Undo. A user-cancelled card shows the feed badge, not a gym-cancelled badge, plus "You reported this cancelled. The gym list still says reserved."

## Phone storage is not the file

The page writes `localStorage` key `tpDash.classHide.v1` on that browser. A saved choice there wins, including Undo setting hidden false on a row the last build hid. That does not write `data/user_overrides.json` and it does not update another device. A browser with no saved choice follows the built `hidden` flag. There is no cross-device sync in this change.

## What the page must show

Hide and Undo are Title Case buttons. After Hide, the row is under "Hidden By You" and Undo is on that row. The class name wraps on its own full-width line. Hide, Cancel, and the badge sit on the next line and do not cover the name. The scope sentence is exactly: "Hide and Undo change visibility only in this browser. Undo does not restore a reservation or change your shared saved choice. Rebuilt pages use that shared choice only when this browser has no saved choice." The row sentence is "You reported this cancelled. The gym list still says reserved." It must not say the gym cancelled it. A failed Hide or failed Undo leaves the row where it was and says "Not saved on this phone. Visibility has not changed." The fixture build stamp is Jan 3, 2099, 11:46 AM CT. It is not a new feed read. No new freshness field is written.

The review fixture is `assembled/current.html`, generated from the real template and the synthetic dataset. `class-hide.html` is an older standalone demo and is not this contract's page. The published `index.html` does not contain this control.
