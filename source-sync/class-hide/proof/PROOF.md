# Generator proof for Total Fitness

Proof only. No release permission. The Style-passed page and generators were not edited.

Code under test is commit `c0d9143227040f682e070fe4746f95f395cf0e25`. `assembled/current.html` remained `d6e51ce0310e6c9fe29825e584e0554149e54ada9c861ea37f9f5442e86f252a`. `runtime/template.html`, `build.py`, and `merge.py` hashes were the same before and after this run.

The harness copied those files and ran `python3 scripts/merge.py` and `python3 scripts/build.py`. It did not call the older assemble helper and did not reuse `assembled/reimport-*.html`. Harness sha256 `0010cc40ef9430491ae96f919de0fe8e68eeee62a53c82767b626b26bae73842`. Captions sit outside `#app` and were removed after each shot. App-only PNG hashes are separate from captioned PNG hashes.

Viewport was 390 CSS pixels, device pixel ratio 2. Clicks used Playwright `click(force=False)` after `elementFromPoint` reached the button. No off-machine request and no dialog.

## Variant A

No `user_overrides.json`. The real build left `2099-01-01|10:00|APEX` visible, feed status `RESERVED`, and the stored Row actual `40×8`.

Hide, reload, and a second merge plus build against a newly written feed that is still `RESERVED` kept the row hidden in the same browser. Storage stayed `{"2099-01-01|10:00|APEX":{"hidden":true}}`. Undo made it visible again and stored `hidden` false. The canonical override file was never created.

Initial page `86f12203c73dcd52cff3de9ff862ec2ff82cba90b18650995b2779a7c5a4ac17`. Rebuilt page `c9b48586d0bb059d953feb19b8d56aece7f0428df9cf38aaba7417827c49925e`. Initial feed `371f595f6d46ad0c374efd94479b91d66dafb406dc30dcc02bb9931281d12c0c`. Fresh feed `ea2b90b79cc978360560490af79becf3b9962a3d01bbbab65861f0a57e56e565`.

## Variant B

The shared file hid APEX before any click. An empty browser showed Hidden By You with Undo. That startup is not a Hide click.

Undo then showed the row in that browser while the file stayed hidden and `provider_cancellation_verified` stayed false. That is local false overriding built true. Hide was clicked only after the row was visible. Reload, then a real merge and build on a new RESERVED feed, kept it hidden in the same browser. Undo showed it again. A second empty browser, with no storage, still showed the built hide.

Initial page `9dbbe05ab1147ddabbef3a3d6a309a8044574f0e6d9803854cd220e1c3c8d2c5`. Rebuilt page `093b2797dec3db4b947e5638120ad976dc75baf2978d4cc7d99a81c9c7a3330c`. Initial feed `4e20634a80953be31e532030d126e03364a625ac8f1ca94dd84d09336e354fdd`. Fresh feed `9d02506363c5c24a0cc9514485f8b80f3aa0fe8fb1cd4d63236f136efaf32a54`.

## What stayed put

At every generated page, the stored actuals were Row `40×8`, Squat `185×5`, and Bench Press `135×8`, `135×8`, `145×6`. Strength stayed `completed` with `status_locked` true. APEX `csv_status` stayed `RESERVED`. `provider_cancellation_verified` was never true.

## What changed on purpose

Variant B's shared override sets the class display status to `CANCELLED` with `cancel_source` `user`, and the APEX workout status to `skipped`. The feed status stays `RESERVED`. That is the synthetic user report, not a gym cancellation.

`first_seen` and `last_seen` are the new CSV file's modification time from this run, `2026-11-07T18:36:13` through `18:36:17`. The fresh file moved `last_seen` by one or two seconds and left `first_seen` in place. Those clocks are not a PushPress or TrainingPeaks read and do not prove freshness.

## Identical app pixels

App-only screenshots match when the screen is in the same state. Captioned files do not match each other. Each caption has its own timestamp.

- A start and A undo: `cb4d0225076b64e8c29182ba217948c746d39e87c899b0a1fd1758e8d7aedfc2`
- A hide, A reload, and A rebuild: `a90d8783078eee3ac5467a0b3f28884cd975a115e4c8e34765c46d5cb6f237c4`
- B empty, B hide, B reload, B rebuild, and the second empty browser: `3d20fd456e2329171e980ac17df8696f10c04ccaeed64d8c61d0c84cb814eff5`
- B local-false visible and B undo: `3388c2204451a294a37b5b7b320cf74e3d6f30dd6a3b022b88fb125619627aa9`

## Limits

This did not touch a live feed, send a message, call a provider, or run a routine. It does not authorize a release. Total Fitness's scoped Style pass was not re-checked here. The day view still draws empty planned rows under the one stored Row set. Those rows are the existing prefill, not extra logged sets.
