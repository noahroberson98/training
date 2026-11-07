# Original versus sanitized mapping

Caller original private files were not uploaded. The hashes below are the pins from `ui-allowlist.json`. The patch was applied only to the sanitized bytes. A fuzz-0 apply on those copies is not an apply to the original hashes.

| Path | Original sha256 | Sanitized sha256 | What the sanitizer changed | What this patch changes |
|---|---|---|---|---|
| scripts/template.html | `e087138ee75b1b488f5d237d7d197d408c3d0251ab5a78a736d655a3bd6c24a8` | `d11572a04a38f337040e970a9f4372c6dd3d08ecba9409b8fffb14524b48000c` | Generalized the user name. Replaced the account slug with `synthetic-owner`. Emptied 1 credential-like literal. Replaced 3 endpoint literals with `example.invalid`. | Hide, Undo, the phone `localStorage` key, and the built `hidden` flag. The empty credential and the disabled endpoints are untouched. |
| scripts/build.py | `1506ec0b0ebefedcbad5200581cacc5858f8d6ac16c6a682465deec6e2f90034` | `c275bcb411c9163331484579df545a270420caa087d30b96087ab4f6ec295b6d` | Generalized the user name. | Reads `data/user_overrides.json` inside `update_class_history`. No routine, network, or guard change. |
| scripts/merge.py | `107ac656de579702c17bf55f7cff3e45b0939be7f95ae927e163fed9bdd4213e` | `7845696c424caa07fcd4bd32674a27de2e7270d1ae90e8a0d52faa0a29b87093` | Generalized the user name. | Reads the same file and holds user-cancelled sets. `status_locked` still wins. |
| scripts/common.py | `081bc82cfbb85b58c776f2d702660bb72dad30d3f54c5bb381e73e8e0a92cd3d` | `1f2002bd7a6da1e88811b90d9d97c3e51c5be09b02de6615fe01bdafc26f14bd` | Generalized the user name. | Adds the override helpers. Does not rewrite earlier comments. |
| scripts/whoop_pair.py | `4b79dfa1c773cf7a479de0f86f77eef6fe5382adb28a843cab0439edc2fb8b0c` | same bytes | None. | None. |

Safer mapping used here: patch the sanitized file with a small hunk, leave the sanitized differences in place, and do not regenerate the whole file. That keeps the emptied credential empty. It is not a claim that the same hunk offsets exist in the original bytes.

`sync_guard.py` and `lock_status.py` are not in this UI handoff and are not patched.
