# Sanitization

The current-data preview is built from the sanitized snapshot `current-training-review-safe-2026-11-06` (safe `index.html` SHA256 `b3a0d7d6e8419efdd8fad99272b62b780612447c9edf18e3bbcfaa31f600ad22`). STORE and EXTRA in the History preview are those bytes, not a re-serialization. The snapshot is a nonpublishable preview. It is not a production send configuration.

The run12 `index.html` on this branch is the repair page and was not edited again. It still has the production send alias, so it is not in the review zip.

The example preview is a separate folder. Its sets are the labeled example fixture, not the six Nov 6 logged sets.

- Candidate SHA256: `c566deaa17c50df31ae77892770a37a58ad46fddb3cd626df33526e957d2fb16`
- Built from the patched template, the store and extra object already embedded in the deployed `index.html` at run8 head `b59aa2b2`, and that page's FormSubmit alias
- Not committed, not zipped, and not published

The example preview differs from that candidate in these ways:

| Item | Candidate | Example preview |
|---|---|---|
| Workout store | Copy of the store already in `index.html` | `tests/fixtures/history_example.json` only |
| Classes, recovery, WHOOP | Copied from that page | Empty |
| `FS_TOKEN` | Production alias | Empty string |
| Finish URL | `https://formsubmit.co/ajax/` plus the alias | `./blocked-outbound/` |
| Sync host | `https://api.github.com` | `./blocked-outbound` |
| Title | `Training · Noah` | `Training · synthetic local preview` |
| Built stamp | `local-candidate` | `example` |
| Banner | None | "Example data. Not a real training log." |
| Leading comment | None | Marks the file as a blocked example |

The sync field still shows the generator's hint `github_pat_…`. That is the same non-token placeholder called out in the run8 manifest. The preview rejects a `github_pat_` or `ghp_` string that continues with token characters. `formsubmit.co`, `api.github.com`, and `REDACTED_FORMSUBMIT_ALIAS` are absent from the preview.

The example fixture uses names such as Example Bench Press and round loads such as 100×8. It is not Noah's log.
