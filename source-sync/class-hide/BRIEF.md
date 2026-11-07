# Class hide brief

For Noah. Synthetic classes only. This is not a release and not a change to the published Training page.

Public Training stays open with no password. JARVIS stays behind its existing protection. The morning routine `trainingpeaks-dashboard-sync` and the afternoon routine `this-gym-afternoon-refresh` are not edited. Those routines rewrite `thisgym_reservations.csv` and `thisgym_schedule.json` from PushPress. There are no separate refresh scripts. The owner reports the afternoon routine no longer overwrites `user_overrides.json`. That routine was not independently verified.

Published site `main` is `794e86cd120100046d8dc510280085edb890d1b5` (Nov 7, 2026, 5:36 AM CT). History publish `dca4a9fe5b0a0aff50fd5207f11e5c687c3e8f12` is the prior publish. Repair `5b682c9312af54e9f24f0eb26bcb99805860f75c` is still an ancestor of `main` and is not rewritten. This branch starts at current `main`. `index.html` is not edited. The public repo contains only the built page, `robots.txt`, `.nojekyll`, and `.srchash`.

## What the published page does today

A gym class card is locked. Cancel appears only for a reserved or waitlisted class that has not started, and it opens the existing local message. It does not remove the card. There is no user-override file and no Hide control. `csv_status` is stored. No field is named `source_asof`. The feed text is the `source` string, with `first_seen` and `last_seen`.

## Contract

`data/user_overrides.json` survives a feed rewrite. The feed files do not. `build.py` reads the override when it writes `data/class_history.json`. `merge.py` reads it when it writes `data/workouts.json`. A missing file changes nothing.

A session key is `date|time|class`, for example `2099-01-01|10:00|APEX`. The real Nov 7 APEX report is not in this fixture. The fixture uses the same shape, with `provider_cancellation_verified` false.

Hide sets `hidden` true and keeps the user cancellation. The gym list can still say reserved. Undo sets `hidden` false only. It does not turn the row into a provider reservation and it does not delete logged sets. A user cancellation is `cancel_source` `user`. It is not `confirmed` and not a gym cancellation. `csv_status` and `source` stay on the feed values. A class that leaves the feed is not, by itself, treated as cancelled. The existing rule that a past class with no override can become completed is unchanged. A user override stops that class from becoming completed.

`sync_guard.py` and `lock_status.py` are not modified. A `status_locked` workout keeps its status.

## Section 9

1. Foundation. For Noah, on his phone, as a real HTML page. No currency. Dark theme, one blue accent. One list, not new tabs. Inputs are the class date, time, name, feed status, feed source text, and the override fields above. Sample rows are the three synthetic bookings in `fixtures/`. Open `class-hide.html` from a local web server. Dates must be `YYYY-MM-DD`. Duplicate keys collapse to one session. A missing override file is an empty set, not an error.

2. KPIs with formulas. Not applicable. This is not a metric dashboard. No KPI cards, trend chart, or click-through totals are added.

3. Comparisons. Not applicable. No growth rate and no partial-period comparison are added.

4. Edge states. A hidden row is not a blank. The booked list says what remains. The hidden list says "No classes hidden by you." when empty. A failed save says "Not saved on this phone. The class is still listed." Missing feed data is not shown as zero classes. Zero-denominator math does not apply.

5. Drilldown and filters. Not applicable. No department, customer, supplier, search, or filtered-row download is added. The only action is Hide or Undo on one row, and the other rows stay put.

6. Charts. Not applicable. No bar, waterfall, or what-if chart is added. The class list is the existing card list.

7. Status is text plus color. "Gym list: Reserved." and "You reported this cancelled. The gym list still says reserved." are words. Color is not the only signal. A user hide is not labeled as a gym cancellation.

8. Reconciliation. Three synthetic rows stay three rows. Hide moves one row between lists and does not drop the others. Logged sets on a matched workout stay. A locked workout status stays. No transfer or double-count rule is added because there is no money ledger.

9. Cutoffs and assumptions. The fixture as-of line is Jan 3, 2099, 11:46 AM CT, taken from the fixture clock, not a new feed read. Assumption on the card: the gym list is still the feed status. A user report is not provider verification. Editable hide has Undo as its reset. The published page's build clock and the 15.3-hour TrainingPeaks warning are a different cutoff and are not moved.

10. Worked check. Feed row `2099-01-01|10:00|APEX` is `RESERVED`. Override is user cancelled, hidden, provider verified false. Expected class record: status `CANCELLED`, hidden true, `csv_status` `RESERVED`, `cancel_source` `user`, provider verified false. The Jan 2 row is absent from the feed and must not become `COMPLETED`. `2099-01-03|09:00|THIS STRENGTH` stays `RESERVED` and visible.

11. Print and export. Not applicable. No print view or export is added. Section 11 of the style guide, the FormSubmit wake, is not used. Hide does not submit a form and does not send mail. No live send test is run.

12. Audit. The shared rule is `apply_user_class_override` and `hold_user_workout_overrides` in `common.py`. Results are in `logs/`. See the audit table below.

## Step 12 results

| Check | Expected | Actual |
|---|---|---|
| Stale reserved feed | Hidden, user cancelled, csv reserved | Pass |
| Missing feed row | Hidden, not completed | Pass |
| Other booking | Reserved, visible | Pass |
| Undo | Visible again, still user cancelled, csv reserved | Pass |
| No override, past missing row | Existing completed rule | Pass |
| Merge of a user-cancelled session | Not completed, set kept | Pass |
| Locked workout | Status stays completed | Pass |
| Merge with no override | Completed workout still merges | Pass |
| Mobile hide, undo, reload, reimport, failed save | As named in the UI log | Pass, 11 checks |
| Production template.html | Not in the handoff | Not run |
| Morning and afternoon routine bodies | Not verified, not changed | Not run |
| Live PushPress, email, publish | Out of scope | Not run |

## Missing from this repo

`template.html` is not in the public repo or this handoff, so the published `index.html` is not patched. The runnable page here is the synthetic `class-hide.html`. Production cards will keep showing a hidden class until that template learns the `hidden` flag. The two routine definitions were not provided and were not changed.
