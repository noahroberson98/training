# JARVIS owner contract

Do not publish this branch. Do not apply the held training-overview bookings change. Do not change the morning or afternoon routines.

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

`thisgym_reservations.csv` and `thisgym_schedule.json` are rewritten by the browser routines from PushPress. Those files are not the override store. A later reserved row, or a missing row, must not bring a hidden session back as a normal booking.

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

## What the page must show

Hide and Undo are Title Case buttons. After Hide, the row is under "Hidden By You" and Undo is on that row. The sentence is "You reported this cancelled. The gym list still says reserved." It must not say the gym cancelled it. A failed save leaves the row where it was and says it was not saved. The as-of time is the feed time already on the record, in CT. No new freshness is written.

The synthetic page `class-hide.html` is the review fixture. The published `index.html` does not contain this control yet because `template.html` was not in the handoff.
