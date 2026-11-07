# Class hide brief

For Noah. Synthetic classes only. This is not a release and not a change to the published Training page. Style review is still required. Nothing here is published, merged, or applied to the private source tree.

Public Training stays open with no password. JARVIS stays behind its existing protection. The morning routine `trainingpeaks-dashboard-sync` and the afternoon routine `this-gym-afternoon-refresh` are not edited. Those routines rewrite `thisgym_reservations.csv` and `thisgym_schedule.json` from PushPress. There are no separate refresh scripts. The owner reports the afternoon routine no longer overwrites `user_overrides.json`. That routine was not independently verified.

Published site `main` is `794e86cd120100046d8dc510280085edb890d1b5` (Nov 7, 2026, 5:36 AM CT). History publish `dca4a9fe5b0a0aff50fd5207f11e5c687c3e8f12` is the prior publish. Repair `5b682c9312af54e9f24f0eb26bcb99805860f75c` is still an ancestor of `main` and is not rewritten. This branch starts at current `main`. `index.html` is not edited.

The standalone `class-hide.html` is an earlier demo. It is not the production UI and it is not the page these results describe. The review page is `assembled/current.html`, filled from the real `scripts/template.html` with an explicitly synthetic dataset.

## Two stores, and the boundary

Hide and Undo on the phone write `localStorage` key `tpDash.classHide.v1` in that browser only. A reload of the same page on that phone keeps the choice. Opening a rebuilt page on that same browser also keeps the choice. The page does not write `data/user_overrides.json`. It does not sync to another phone, another browser, or another device.

`data/user_overrides.json` is the canonical file. `build.py` reads it while writing `data/class_history.json`. `merge.py` reads it while writing `data/workouts.json`. A feed rewrite can replace `thisgym_reservations.csv` and `thisgym_schedule.json`. It does not delete the override file. A newly built page hides a class when that file says hidden, even with empty browser storage. A phone Undo does not change the file, so a different device still shows the built hide until the file itself is edited and the page is built again.

## What the published page does today

A gym class card is locked. Cancel appears only for a reserved or waitlisted class that has not started, and it opens the existing local message. It does not remove the card. The published `index.html` still has no Hide control. `csv_status` is stored. No field is named `source_asof`. The feed text is the `source` string, with `first_seen` and `last_seen`.

## Contract

A session key is `date|time|class`, for example `2099-01-01|10:00|APEX`. The real Nov 7 APEX report is not in this fixture. The fixture uses the same shape, with `provider_cancellation_verified` false.

Hide sets `hidden` true and keeps the user cancellation. The gym list can still say reserved. Undo sets `hidden` false only. It does not turn the row into a provider reservation and it does not delete logged sets. A user cancellation is `cancel_source` `user`. It is not `confirmed` and not a gym cancellation. `csv_status` and `source` stay on the feed values. A class that leaves the feed is not, by itself, treated as cancelled. The existing rule that a past class with no override can become completed is unchanged. A user override stops that class from becoming completed.

`sync_guard.py` and `lock_status.py` are not modified. A `status_locked` workout keeps its status. The emptied credential literal in the sanitized template stays empty. The `example.invalid` endpoints stay disabled. No live request left the test machine.

## Section 9

1. Foundation. For Noah, on his phone, as the real template filled into `assembled/current.html`. No currency. Dark theme, one blue accent. The day list and the week columns are the existing views. Hidden By You is a section on those views, not a new tab. Inputs are the class date, time, name, feed status, feed source text, and the override fields above. Sample rows are the synthetic bookings in `fixtures/`, plus one synthetic Personal Training class, an Upper Body workout, a locked Strength workout, and a user-cancelled APEX workout that still has its logged set. Serve `assembled/` from a local web server and open `current.html?tab=workout&day=2099-01-03`. Dates are `YYYY-MM-DD`. Duplicate keys collapse to one session. A missing override file is an empty set, not an error.

2. KPIs with formulas. Not applicable. This change adds no KPI card, trend total, or click-through metric.

3. Comparisons. Not applicable. No growth rate and no partial-period comparison are added.

4. Edge states. A hidden row is not a blank. The booked list shows the classes still listed that day. The hidden list says "No classes hidden by you." when empty. A failed save says "Not saved on this phone. The class is still listed." and the row stays where it was. A missing feed row is not shown as a completed class and is not dropped from history when an override exists. Zero-denominator math does not apply.

5. Drilldown and filters. Not applicable. No department, customer, supplier, search, or filtered-row download is added. The only new action is Hide or Undo on one class. The other classes and the logged sets stay put.

6. Charts. Not applicable to this change. No bar, waterfall, or what-if chart is added. The existing History estimate chart is unchanged and still draws for the synthetic Bench Press, Row, and Squat rows.

7. Status is text plus color. The gym badge stays the feed word, "Reserved." The sentence is "You reported this cancelled. The gym list still says reserved." Color is not the only signal. A user hide is not labeled as a gym cancellation. Buttons are Title Case: Hide, Undo.

8. Reconciliation. The synthetic class rows stay the same rows. Hide moves one row between the booked list and Hidden By You and does not drop the others. The Row set at 40 lb, the Squat set at 185 lb, and the Bench Press sets at 135 lb and 145 lb stay. The locked Strength workout stays Completed. The APEX workout stays Skipped because the user reported it, and that is not a provider confirmation. No money ledger is added.

9. Cutoffs and assumptions. The fixture as-of line is Jan 3, 2099, 11:46 AM CT, written into the page as the build stamp from the fixture clock. Assumption on the card: the gym list is the feed `csv_status`. A user report is not provider verification. Undo resets visibility only. The published page's build clock and the TrainingPeaks warning are a different cutoff and are not moved. Phone storage and the override file are different stores, as stated above.

10. Worked check. Feed row `2099-01-01|10:00|APEX` is `RESERVED`. Override is user cancelled, hidden, provider verified false. Built class record: status `CANCELLED`, hidden true, `csv_status` `RESERVED`, `source` `synthetic feed`, `cancel_source` `user`, provider verified false. The Jan 2 row is absent from the feed and stays `CANCELLED`, not `COMPLETED`. `2099-01-03|09:00|THIS STRENGTH` stays `RESERVED` and visible until a Hide on that phone.

11. Print and export. Not applicable. No print view or export is added. Section 11 of the style guide, the FormSubmit wake, is not used. Hide does not submit a form and does not send mail. No live send test is run.

12. Audit. The shared rule is `apply_user_class_override` and `hold_user_workout_overrides` in `common.py`. The page rule is `classHidden` in `template.html`: a phone record wins on that browser, otherwise the built `hidden` flag wins. Results below are from `logs/test_overrides.log` and `logs/test_template_mobile.log`, run against `assembled/current.html`, `assembled/reimport-reserved.html`, and `assembled/reimport-missing.html`. Screenshots are `shots/mobile-before.png`, `shots/mobile-hidden.png`, `shots/mobile-undo.png`, and `shots/mobile-save-failed.png`.

## Step 12 results

| Check | Expected | Actual |
|---|---|---|
| Stale reserved feed, built page, empty browser storage | Hidden, user cancelled, csv reserved, source unchanged, provider false | Pass. `cancel_source` user, `hide-store` built |
| Missing feed row | Hidden, status CANCELLED, not COMPLETED, csv reserved | Pass on `reimport-missing.html` with empty storage |
| Other booking | Reserved and visible | Pass. `2099-01-03\|09:00\|THIS STRENGTH` stays listed |
| Hide, then Undo on the hidden row | Row leaves the booked list, Undo is the button, Undo puts it back | Pass |
| Reload | Phone `localStorage` still has the hide | Pass. Key `tpDash.classHide.v1` |
| Same browser, rebuilt page whose feed is still RESERVED | Phone hide still applied | Pass. `hide-store` phone |
| Empty browser, same rebuilt reserved feed | File hide still applied | Pass. `hide-store` built. The feed did not restore the booking |
| Undo of a built hide | Visible again, status still CANCELLED, csv still RESERVED, provider still false, Row set still 40 lb | Pass. Visibility only |
| Failed save | "Not saved on this phone. The class is still listed." and the row stays booked | Pass. Squat 185 lb still on the page |
| Locked workout | Strength stays completed and `status_locked` | Pass. 185 lb × 5 remains |
| Upper Body and Personal Training | Bench Press sets and the PT line remain | Pass. 135 lb × 8, 145 lb × 6, Personal Training |
| History | Bench Press, Row, and Squat still listed, with the Jan 6 loads | Pass |
| Week card | Lock stays, Hide removes that card from the week column | Pass |
| Off-machine requests, dialogs, page errors | None | Pass. 24 checks, 0 failures |
| Python override suite | Stale, missing, undo, no-override completed rule, merge sets, locked status, plain merge | Pass. 12 checks |
| Original private files | Not uploaded | Fuzz 0 was run on the sanitized copies only. That does not prove the patch applies to the original hashes |
| Morning and afternoon routine bodies | Not verified, not changed | Not run |
| Live PushPress, email, publish, source apply | Out of scope | Not run |

## What is still true

The published `index.html` does not contain Hide. These patches are not applied to the private originals. The credential literal stays empty. Style review of this template-generated fixture is still required before any publish.
