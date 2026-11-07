# Milestone proof

This run does not replace `proof/out` or the archive `6a05a18ac26b9a18754d3530cedac3123b7f8e42e2d21588b450fecf3ac060df`. Those files are the earlier run, which checked completed sets and the locked Strength workout only at the four generator checkpoints. Nothing in that archive was edited to add assertions after the fact.

Implementation pin remains `c0d9143227040f682e070fe4746f95f395cf0e25`. `build.py`, `merge.py`, `template.html`, and `assembled/current.html` (`d6e51ce0310e6c9fe29825e584e0554149e54ada9c861ea37f9f5442e86f252a`) matched that commit before and after this run. Harness `proof/run_milestone_assertions.py` sha256 `ae3f568b2cc3ec02a55f8072c972ced90f9be5896581a067d378586a202597d7`. The first harness file is unchanged at `0010cc40ef9430491ae96f919de0fe8e68eeee62a53c82767b626b26bae73842`.

`ordered-state.json` has 13 loaded-page checks: A start, Hide, reload, rebuild, Undo; B empty browser, before Undo, first Undo, Hide, reload, rebuild, Undo, and the second empty browser. Each one records the five stored actuals, the two identical Bench Press `135×8` rows as separate indexes, Strength `completed` with `status_locked` true, APEX `csv_status` `RESERVED`, and the override file. Variant A has no override file at every step. Variant B's file stays 482 bytes, sha256 `b5603ec54333bbb3078cff8091201edd883ab150908daebabf3cee70bef85009`, with baked `cancel_source` `user` and `provider_cancellation_verified` false. Click records include `"force": false` from the argument passed to `locator.click`, plus the hit-test result. There were five such clicks.

The stored sets have no `id`, `set_id`, or `eid`. Identity in this log is workout, label, name, and index. Variant A does not store a provider field on the class; the card attribute is the string `false`. Variant B stores boolean false.

App-only PNG hashes for the same screen match the earlier capture. These files were written again by this browser run. Captioned PNGs differ because the harness timestamp differs. `first_seen` and `last_seen` are this run's CSV file times, not a live provider read. No Style re-review and no release.
