# Pins

UI handoff zip `bbaf85694ebdc76fbbdf31d4fb54648856d42271f62289844df9105731c63f56`, 65,135 bytes. The uploaded allowlist matches the zip member `ui-allowlist.json`. Scan result was PASS, static only. Template endpoints in that copy are `example.invalid`. One credential-like literal is empty. It is not restored here and its original value was not requested.

The earlier code handoff zip was `9895e96e2cb87e2cb2cede9c4f29548bbede5fb7c89faec2f980b267f40732b0`, 22,927 bytes. Build and merge original pins are the same hashes as that bundle.

| File | Original sha256 | Sanitized sha256 this patch applies to | Patched sha256 |
|---|---|---|---|
| scripts/template.html | `e087138ee75b1b488f5d237d7d197d408c3d0251ab5a78a736d655a3bd6c24a8` | `d11572a04a38f337040e970a9f4372c6dd3d08ecba9409b8fffb14524b48000c` | `cc1a471c89f3949aaa4393d1d8fd26efe9d300a37c013bfe29e5401b8ff54091` |
| scripts/common.py | `081bc82cfbb85b58c776f2d702660bb72dad30d3f54c5bb381e73e8e0a92cd3d` | `1f2002bd7a6da1e88811b90d9d97c3e51c5be09b02de6615fe01bdafc26f14bd` | `225e36db110345475243309298c60c8367e76bd8a31c4860402ea8be7228c77a` |
| scripts/build.py | `1506ec0b0ebefedcbad5200581cacc5858f8d6ac16c6a682465deec6e2f90034` | `c275bcb411c9163331484579df545a270420caa087d30b96087ab4f6ec295b6d` | `419709eb905385299b4a4fc0a7d78eeefc7e5551cb6526f6196a721481201b70` |
| scripts/merge.py | `107ac656de579702c17bf55f7cff3e45b0939be7f95ae927e163fed9bdd4213e` | `7845696c424caa07fcd4bd32674a27de2e7270d1ae90e8a0d52faa0a29b87093` | `b66b724a0bc6a92c5891334c9b8b34deb5e4b83e6e8f60b55afa283bc1d259b0` |
| scripts/whoop_pair.py | `4b79dfa1c773cf7a479de0f86f77eef6fe5382adb28a843cab0439edc2fb8b0c` | byte-identical | not patched |

`logs/fuzz0.log` records `patch -p1 --fuzz=0` against those sanitized bytes. Each file matched the patched runtime copy after apply. The original files were not uploaded, so fuzz 0 on the sanitized copies does not prove the patch applies to the original hashes. The hunks do not rewrite the sanitized name comments, do not put the credential back, and do not put the real endpoints back.

## Assembled fixture

Filled from the patched template with synthetic data only. Build stamp `Jan 3, 2099, 11:46 AM CT`.

| Page | Bytes | sha256 |
|---|---|---|
| assembled/current.html | 168002 | `7e706e2150f55e5d72a8e7b12eb89370310aaf3668f47f7e747c3bf89426318f` |
| assembled/reimport-reserved.html | 168012 | `a4b857dd45d9df37a229d969741068217fde72eb2aa0d683f3e3db71172a8027` |
| assembled/reimport-missing.html | 167831 | `7230b7728d03cfbdc3271237cc3f298498da4b88b5a676821cfc39ed472e4a31` |
| assembled/live-shape.html | 166888 | `31b5f0feaec428ec73b712a446526b5861213aecb0f4e358b57af3e13227fac4` |

`d6e51ce0310e6c9fe29825e584e0554149e54ada9c861ea37f9f5442e86f252a` is the earlier Style-passed page and does not cover `live-shape.html`. Fuzz 0 for this change is `logs/fuzz0-live-shape.log`, against the sanitized copies only. The Jan 3, 2099, 11:46 AM CT line is a fixture stamp, not a freshness proof.

Fixture `fixtures/user_overrides.json` is `a4f4b75dbd3bcf8039498a137638ea3a93be414aee9456f1449656d3b21a716f`. It is a contract example, not the owner's private file and not a provider confirmation.

Public `main` `794e86cd120100046d8dc510280085edb890d1b5`. This branch's parent for the earlier override consumers is `c7f12ffa1754f3a0cac9e90e666a46f57685ad1a`.
