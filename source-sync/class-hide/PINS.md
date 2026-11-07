# Pins

Handoff zip `9895e96e2cb87e2cb2cede9c4f29548bbede5fb7c89faec2f980b267f40732b0`, 22,927 bytes. Allowlist and scan report match the zip members. Scan result was PASS with the stated static-scan limitation.

| File | Original source sha256 | Sanitized bytes this patch applies to |
|---|---|---|
| scripts/common.py | `081bc82cfbb85b58c776f2d702660bb72dad30d3f54c5bb381e73e8e0a92cd3d` | `1f2002bd7a6da1e88811b90d9d97c3e51c5be09b02de6615fe01bdafc26f14bd` |
| scripts/build.py | `1506ec0b0ebefedcbad5200581cacc5858f8d6ac16c6a682465deec6e2f90034` | `c275bcb411c9163331484579df545a270420caa087d30b96087ab4f6ec295b6d` |
| scripts/merge.py | `107ac656de579702c17bf55f7cff3e45b0939be7f95ae927e163fed9bdd4213e` | `7845696c424caa07fcd4bd32674a27de2e7270d1ae90e8a0d52faa0a29b87093` |
| scripts/sync_guard.py | `783450eba838bded83a7b02682762bf982d392b32b9390a0297df73a2ad3a386` | unchanged `ac449ebd615ebd8f3dba553915410b04c3b721d2ec6d9c0608cc34121a0c6785` |
| scripts/lock_status.py | `1b293c536e1caafdaf0d374a67c78a7471554291f7dce3ad708084329d832447` | unchanged `33a42707c5687e25c13672f045dd19c6863739b913cf1e8355b07f59f5bbbef8` |
| scripts/whoop_pair.py | `4b79dfa1c773cf7a479de0f86f77eef6fe5382adb28a843cab0439edc2fb8b0c` | byte-identical, not patched |

The patches apply with fuzz 0 to the sanitized bytes above. The original files were not in the handoff, so the patches were not applied to those hashes here. The hunks do not rewrite the generalized name comments.

Fixture `fixtures/user_overrides.json` is `a4f4b75dbd3bcf8039498a137638ea3a93be414aee9456f1449656d3b21a716f`. It is a contract example, not the owner's private file and not a provider confirmation.
