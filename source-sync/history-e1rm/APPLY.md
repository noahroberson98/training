# Apply on the local generator

The canonical generator is the local-only git checkout at `training-dashboard`. Do not `git reset` or `git checkout` those dirty files. This patch is against the current template bytes plus the run8 template patch. It does not edit `build.py`, `publish.sh`, or any uncovered dirty file.

From the training-dashboard root, after the run8 patches are applied:

```
patch -p1 < template.html.patch
cp files/scripts/preview_history.py scripts/preview_history.py
cp files/tests/test_e1rm_history.py tests/test_e1rm_history.py
mkdir -p tests/fixtures
cp files/tests/fixtures/history_example.json tests/fixtures/history_example.json
python3 tests/test_e1rm_history.py
```

`template.html.patch` does not change the `FS_TOKEN` line. A trial apply onto the run8 template left `REDACTED_FORMSUBMIT_ALIAS` in the sanitized copy and left `https://formsubmit.co/ajax/` and `https://api.github.com` in the generator source.

Example preview, not a release:

```
python3 scripts/preview_history.py --out /tmp/history-preview
python3 -m http.server 8765 --bind 127.0.0.1 --directory /tmp/history-preview
```

Open `http://127.0.0.1:8765/open.html`.

Do not point sync at a real host. Do not run `publish.sh` for this handoff. A later authorized rebuild from the current real store is what publishes History. Replacing `index.html` with the example page, or with a candidate built from the copy of the store already in the deployed page, is not that rebuild.
