# Apply on the local generator

Do not reset the local training-dashboard. Its git repo has no remote. This History patch applies only to the updated repair template, with fuzz 0. A different preimage is the wrong base.

## Hashes

| File | SHA256 |
|---|---|
| Run8 patched `scripts/template.html` | `e3a379d4a9dcf7c1b54b8a29096db52abb6840ca3171a89d11d2e6560c7913dd` |
| After `patches/run12-known-load.patch` | `d5946907beb0dbaff8b1d20a8b7d5c33710423270ac0e9ee9af6aa384529a7f5` |
| After `patches/template.html.patch` | `5ad77b37042ab419d10c0823915e6376a7277276e9210b7e2db212a7f29fc555` |
| `patches/run12-known-load.patch` | `02c8c02d8c80124fdad53fa24839aed000b039382716a7627608c75b1179d41a` |
| `patches/template.html.patch` | `ac5e2921a4bb097068cbdbf8d04538343c06e8a7e91d942d8a7520a36613a4cf` |

The run12 patch is the known-load volume and “Pounds assumed” logic from repair commit `7d00bb7417ada9aecb4523dd0189b91068c8d8fd`, reconstructed onto the run8 template so a later generator rebuild keeps it. It does not add the History chart. The History patch is the diff from that updated template to the History template.

## Commands

From the training-dashboard root, when `scripts/template.html` hashes to the run8 value above:

```
sha256sum scripts/template.html
patch -p1 --fuzz=0 < patches/run12-known-load.patch
sha256sum scripts/template.html
patch -p1 --fuzz=0 < patches/template.html.patch
sha256sum scripts/template.html
```

Stop if either `patch` reports a failed hunk or a hash does not match the table. Do not rerun with fuzz.

If `scripts/template.html` already hashes to `d5946907beb0dbaff8b1d20a8b7d5c33710423270ac0e9ee9af6aa384529a7f5`, skip the run12 patch and apply only `template.html.patch`.

Neither patch changes the `FS_TOKEN` line.

Then:

```
cp files/scripts/preview_history.py scripts/preview_history.py
cp files/scripts/preview_current.py scripts/preview_current.py
cp files/tests/test_e1rm_history.py tests/test_e1rm_history.py
cp files/tests/test_e1rm_current.py tests/test_e1rm_current.py
cp files/tests/test_e1rm_exact.py tests/test_e1rm_exact.py
mkdir -p tests/fixtures
cp files/tests/fixtures/history_example.json tests/fixtures/history_example.json
HISTORY_PATCH="$PWD/patches/template.html.patch" python3 tests/test_e1rm_history.py
```

Run that from the handoff directory so `patches/template.html.patch` resolves. If the test instead runs inside the generator checkout, set `HISTORY_PATCH` to the absolute path of that same patch. The test does not print the token. Without the patch file it still checks that a sentinel token is cleared and that a patch mentioning `FS_TOKEN` would fail, and it prints a NOTE that the patch file was not beside the checkout.

`test_e1rm_current.py` takes the exact sanitized page and does not rebuild it:

```
python3 tests/test_e1rm_current.py /path/to/safe.html /tmp/exact-shots
```

It hashes that file before and after. Do not publish the page.

Do not run `publish.sh` for this handoff. The deployed `index.html` on this branch stays the run12 page. History reaches the site only through a later authorized rebuild after Style clears the corrected current-input build.
