# Class hide brief

For Noah. Synthetic classes only. This is not a release and not a change to the published Training page. Style review is still required. Nothing here is published, merged, or applied to the private source tree.

Public Training stays open with no password. JARVIS stays behind its existing protection. The morning routine `trainingpeaks-dashboard-sync` and the afternoon routine `this-gym-afternoon-refresh` are not edited. Those routines rewrite `thisgym_reservations.csv` and `thisgym_schedule.json` from PushPress. There are no separate refresh scripts. The owner reports the afternoon routine no longer overwrites `user_overrides.json`. That routine was not independently verified.

Published site `main` is `794e86cd120100046d8dc510280085edb890d1b5` (Nov 7, 2026, 5:36 AM CT). History publish `dca4a9fe5b0a0aff50fd5207f11e5c687c3e8f12` is the prior publish. Repair `5b682c9312af54e9f24f0eb26bcb99805860f75c` is still an ancestor of `main` and is not rewritten. This branch starts at current `main`. `index.html` is not edited.

The standalone `class-hide.html` is an earlier demo. It is not the production UI and it is not the page these results describe. The current safe page is `assembled/current.html`, 168,002 bytes, sha256 `7e706e2150f55e5d72a8e7b12eb89370310aaf3668f47f7e747c3bf89426318f`. The live-shape page is `assembled/live-shape.html`, 166,888 bytes, sha256 `31b5f0feaec428ec73b712a446526b5861213aecb0f4e358b57af3e13227fac4`. Style's earlier pass on `d6e51ce0310e6c9fe29825e584e0554149e54ada9c861ea37f9f5442e86f252a` does not cover this card. No approval is claimed.

## Two stores, and the boundary

The screen says: "Hide and Undo change visibility only in this browser. Undo does not restore a reservation or change your shared saved choice. Rebuilt pages use that shared choice only when this browser has no saved choice." That sentence does not name a file.

On this browser, Hide and Undo write `localStorage` key `tpDash.classHide.v1`. A saved choice here wins over the hide baked into the page. Undo of a built-hidden row shows that row on this browser and leaves the shared choice unchanged. A browser with no saved choice follows the hide baked by the last build. The page does not write the shared file and does not update another browser or device.

The generators read `ROOT/data/user_overrides.json`, where ROOT is the parent of `scripts/`. On a training-dashboard install that is `training-dashboard/data/user_overrides.json`. The canonical fitness file is a different path. This branch does not install a symlink and does not change either live path. `WIRING.md` states the staged expectation. A temp-tree test opens a synthetic symlink and does not create `/workspace/training-dashboard`.

`csv_status` and `provider_status` are the provider baseline. `feed_status` is the raw column on this read. An unverified user cancel does not replace an established baseline, and it does not turn a missing baseline into RESERVED or into a copied CANCELLED. That case is `unknown`. A feed change with no user-cancel explanation can update the baseline, and that update is still not `provider_cancellation_verified`. A user override never sets that flag true.

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

4. Edge states. A hidden row is not a blank. The booked list shows the classes still listed that day. The hidden list says "No classes hidden by you." when empty. A failed Hide or a failed Undo says "Not saved on this phone. Visibility has not changed." and the row stays where it was. A missing feed row is not shown as a completed class and is not dropped from history when an override exists. Zero-denominator math does not apply.

5. Drilldown and filters. Not applicable. No department, customer, supplier, search, or filtered-row download is added. The only new action is Hide or Undo on one class. The other classes and the logged sets stay put.

6. Charts. Not applicable to this change. No bar, waterfall, or what-if chart is added. The existing History estimate chart is unchanged and still draws for the synthetic Bench Press, Row, and Squat rows.

7. Status is text plus color. For a user report that the provider has not confirmed, the badge is the provider baseline, and the sentence is "You reported this cancelled. The provider has not confirmed it. The gym list still says reserved." When the baseline is unknown, the badge says Unknown and the sentence does not claim reserved. Color is not the only signal. Buttons are Title Case: Hide, Undo. The live-shape card was readable at 390 CSS pixels. This wording needs a new Style check.

8. Reconciliation. The synthetic class rows stay the same rows. Hide moves one row between the booked list and Hidden By You and does not drop the others. The Row set at 40 lb, the Squat set at 185 lb, and the Bench Press sets at 135 lb and 145 lb stay. The locked Strength workout stays Completed. The APEX workout stays Skipped because the user reported it, and that is not a provider confirmation. No money ledger is added.

9. Cutoffs and assumptions. The fixture build stamp is Jan 3, 2099, 11:46 AM CT. It is the synthetic stamp written into the page. It is not a TrainingPeaks or PushPress read, and it does not certify feed freshness. Some class rows carry synthetic `first_seen` and `last_seen` of 2099-01-04T12:00:00 from the fixture history clock. Those values are later than the build stamp. They are not a chronology check and not a new provider observation. Assumption on the card: the gym list is the feed `csv_status`. A user report is not provider verification. Undo on this browser changes visibility only. The published page's build clock and the TrainingPeaks warning are a different cutoff and are not moved. Phone storage and the shared file are different stores, as stated above.

10. Worked check. Feed row `2099-01-01|10:00|APEX` is `RESERVED`. Override is user cancelled, hidden, provider verified false. Built class record: status `CANCELLED`, hidden true, `csv_status` `RESERVED`, `source` `synthetic feed`, `cancel_source` `user`, provider verified false. The Jan 2 row is absent from the feed and stays `CANCELLED`, not `COMPLETED`. `2099-01-03|09:00|THIS STRENGTH` stays `RESERVED` and visible until a Hide on that phone.

11. Print and export. Not applicable. No print view or export is added. Section 11 of the style guide, the FormSubmit wake, is not used. Hide does not submit a form and does not send mail. No live send test is run.

12. Audit. The shared rule is `apply_user_class_override` and `hold_user_workout_overrides` in `common.py`. The page rule is `classHidden` in `template.html`: a saved choice in this browser wins, including a local false over a built true. With no saved choice, the built hide is what shows. Results below are from `logs/test_overrides.log` and `logs/test_template_mobile.log`, run against `assembled/current.html` (`d6e51ce0310e6c9fe29825e584e0554149e54ada9c861ea37f9f5442e86f252a`), `assembled/reimport-reserved.html`, and `assembled/reimport-missing.html`. The prior candidate `80229dc37c082b1a87b845cb4fd718d5784d04e47055767f12305833aac6fc9e` is the before state in the table. Screenshots are `shots/mobile-before.png`, `shots/mobile-hidden.png`, `shots/mobile-undo.png`, `shots/mobile-save-failed.png`, and `shots/mobile-undo-save-failed.png`. The first rerun is kept at `logs/test_template_mobile-attempt1.log`. It failed one harness check. The final log does not replace that file.

## Step 12 results

| Check | Before `80229dc3` | After `d6e51ce0` |
|---|---|---|
| Scope sentence | Named `user_overrides.json` and said a rebuilt page hides whenever that file says hidden | Exact owner sentence. Visible page text has no filename. Pass |
| Local false versus built true | Code already revealed a built-hidden row after Undo, but the sentence did not say so | Undo shows the row here, status stays CANCELLED, csv stays RESERVED, provider stays false, Row set stays 40 lb. Empty storage on `reimport-reserved.html` still hides it. Pass |
| Class name at 390 CSS px, device pixel ratio 2 | THIS STRENGTH rendered with an ellipsis beside Hide, Cancel, and Reserved | Name box x 104, y 405, 248 by 21.8. Painted text 114.7 by 20. `text-overflow` clip, `white-space` normal, `scrollWidth` 248 equals `clientWidth`. Hide 58.1 by 38.3, Cancel 93.8 by 31.4, Reserved below them. No overlap. `elementFromPoint` hits the buttons. Same box on the Undo and failed-Hide frames. Week name box 228 by 16.3, painted text 99.1 wide, not clipped. Pass |
| Failed Hide | "The class is still listed." Row stayed booked | "Not saved on this phone. Visibility has not changed." Row stays booked and readable. Pass. Shot `mobile-save-failed.png` |
| Failed Undo, built hide | Not covered. The old shared sentence would have said the class was still listed | Real click with storage throwing. APEX stays hidden, `hide-store` built, storage bytes unchanged, cancel user, provider false, csv RESERVED. Pass. Shot `mobile-undo-save-failed.png` |
| Failed Undo, phone hide | Not covered | Real click after a saved Hide. THIS STRENGTH stays hidden, storage stays `hidden` true, status and csv stay RESERVED, provider false. Pass |
| Later successful save | Not asserted against the warning | Warning count returns to 0. Pass |
| First rerun |  | `logs/test_template_mobile-attempt1.log` failed the week hit check because it required a 24px height. The existing week Cancel chip is 23.4 CSS px tall, `elementFromPoint` reached it, and the name was already unclipped. The floor is now 20. That failure file is unchanged |
| Final mobile log | 24 checks on the previous page | 31 checks, 0 failures, in `logs/test_template_mobile.log`. Network log `logs/network.json` has no off-machine URL |
| Missing feed row | Hidden, not completed | Pass on `reimport-missing.html` with empty storage |
| Locked workout, Upper Body, PT, History | Sets and statuses stayed | Pass. Strength completed and locked, 185 lb × 5. Bench 135 and 145. Personal Training line remains. History lists Bench Press, Row, and Squat |
| Python override suite | 12 checks | Pass, 12 checks, `logs/test_overrides.log` |
| Fixture clock | Build stamp Jan 3, 2099, 11:46 AM CT | Same stamp. `first_seen` and `last_seen` of 2099-01-04 remain the synthetic history clock. Not a freshness proof |
| Original private files | Not uploaded | Fuzz 0 on the sanitized copies only. `logs/fuzz0.log`. That does not prove an apply to the original hashes |
| Morning and afternoon routines, live provider, email, publish | Not run | Not run |

## Live-shape results

`logs/test_live_shape-attempt1.log` is the failure before the fix: the user-mutated CANCELLED column replaced the RESERVED baseline. `logs/test_live_shape-attempt2.log` is a later assertion miss on the unrendered source string. `logs/test_live_shape.log` is the passing run. The 13-step synthetic proof is not clearance for this shape.

| Check | Expected | Actual |
|---|---|---|
| Established RESERVED plus user-mutated CANCELLED column | `csv_status` and `provider_status` stay RESERVED, `feed_status` is CANCELLED, display is user cancel, provider flag false | Pass |
| Feed CANCELLED with no user report | Baseline becomes CANCELLED, not labeled user or confirmed, provider flag not true | Pass |
| No baseline plus user-mutated CANCELLED | `unknown`, not a hardcoded RESERVED | Pass |
| Established provider CANCELLED | Stays CANCELLED | Pass |
| Other booking | Stays RESERVED | Pass |
| Sets and lock | Row 40×8, Squat 185×5 locked completed, Bench 135×8 twice plus 145×6 | Pass |
| Synthetic symlink | Generators read it inside a temp tree only | Pass |
| Hidden card at 390 | User-report sentence, Reserved badge, provider false, Undo, failed save | Pass. Shots `live-shape-hidden.png`, `live-shape-undo.png`, `live-shape-save-failed.png` |

## What is still true

The published `index.html` is unchanged. The private originals are not patched. The live symlink is not installed. The credential literal stays empty. The new card still needs Style review. No approval is claimed, and no release is authorized.
