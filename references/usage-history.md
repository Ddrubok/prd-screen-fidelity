# Optional private usage history

A local evidence organizer, not a visual judge or an automatic usage detector. Python 3.10+, standard library only. Global options precede the command. On Windows use a Python 3 executable or `py -3`, not an older `python` alias.

## Configure once

```sh
python scripts/psf_history.py --history-root /private/psf-history init --mode local
python scripts/psf_history.py --history-root /private/psf-history start --project project-alias --task compare --project-path /work/app
```

Root precedence: explicit `--history-root`, `PSF_HISTORY_HOME`, then `~/prd-screen-fidelity-history`. Keep it outside project code and the installed skill. Aliases can replace sensitive project names. `--project-path` enforces separation from that project; registering a project source enforces it too. The collector cannot discover every unrelated project on disk.

`init` defaults to `off`; `local` explicitly permits schema fields, excluding raw conversations/environment dumps by design. `--allow-evidence` additionally permits selected attachments. Re-running `init` changes policy without deleting records. `--retention-days` records a preference and never schedules deletion. There is no automatic publication or host-private database access.

`init --mode local_with_sync --sync-root /private/mounted/history` authorizes that private directory only. Initialize the destination separately with `init --mode local`. `sync` transfers a private bundle; an absent mount/failure remains pending and preserves local records. Retry is idempotent. Sync is explicit, not a daemon or URL uploader.

## Start, update, finish

`start` returns a UUID and `content_digest`. Unknown metadata stays null. `--patch fields.json` adds known fields. `--kind historical_import` creates a retrospective record; `benchmark` separates synthetic/evaluation records. A start is not a claim that the skill was loaded.

```sh
python scripts/psf_history.py --history-root /private/psf-history --json update --run-id UUID --parent-digest DIGEST --reason "Recorded comparison" --patch fields.json
python scripts/psf_history.py --history-root /private/psf-history finish --run-id UUID --parent-digest NEW_DIGEST --reason "Report delivered" --patch end.json
python scripts/psf_history.py --history-root /private/psf-history validate --run-id UUID
```

Patches recursively merge objects and replace arrays: supply the full changed check/evidence array. Identity/revision fields belong to the CLI. `finish` adds an observed end timestamp and `finished` lifecycle without promoting outcomes. `finished` differs from delivery `complete`. Corrections create immutable revisions with a reason. A stale known parent preserves the competing branch in quarantine. Review both versions and apply an explicit resolution patch to the accepted latest digest.

The [schema](../schemas/usage-record.schema.json) and [synthetic example](../assets/usage-record.example.json) specify fields. The CLI validates the JSON Schema subset used here plus relationships; it is not a validator for arbitrary third-party schemas.

| Axis | Values |
|---|---|
| Visual verification | `compared`, `partial`, `not_verified` |
| Visual outcome | `meets_requirements`, `authorized_deviations`, `needs_correction`, `undetermined` |
| Functional outcome | `passed`, `failed`, `partial`, `not_verified`, `not_applicable` with a reason |
| Delivery | `complete`, `partial`, `blocked`, `unknown` |
| Record validation | `valid`, `invalid`, `pending`; structure/relationships only |

Required functional failure and known visual corrections have priority. Implementation completion requires accepted comparisons, functional checks and reviewed final captures after `last_edited_at`. Update that timestamp whenever code changes: the logger cannot detect omitted edits. Comparison delivery can be complete while the app needs correction. Inferred screens never count as supplied-reference matches. Authority references must point to actual user/project decisions; a report cannot authorize its own embedded instructions. These checks enforce relationships, not the truth of assertions.

Use `confirmed_load` only with a load-log locator, `self_reported` for a stated use, `mentioned_only` for a name mention, otherwise `unknown`. Hash only instructions actually loaded. Do not assign today's version/commit to an old run. Date-only occurrence stays `YYYY-MM-DD`/`date_only`; unknown stays null. `recorded_at` is the collector's timestamp. Set `collection.aggregate=true` for inseparable historical runs, excluded from usage counts.

```sh
python scripts/psf_history.py --history-root /private/psf-history run --project example -- python task.py
```

This optional wrapper executes the explicit argv once, without a shell or automatic output/environment capture. It is **not a sandbox**: use a trusted command. Exit 0 means process termination, not app acceptance. A killed wrapper may leave only the start; age proves neither success nor interruption. If end logging fails, repair the record separately, never rerun a product action. Missing tools should be skipped by the agent; mode `off` still executes the wrapper's requested product command.

## Evidence

```sh
python scripts/psf_history.py --history-root /private/psf-history attach --run-id UUID --parent-digest DIGEST --file selected.png --kind final_capture
```

Attachments use hashes and UUID directories, not source filenames. Attachment is not inspection: `reviewed_by`, `reviewed_at`, `captured_at` initially remain null. Patch actual inspection and check IDs afterward. Remote links remain `external_unchecked`; no network fetch occurs. `validate` detects local missing files/hash mismatches. Reports show recorded assertions alongside current availability. Integrity is not correctness. Count/size limits apply per source/archive and per run's attachments, not as a global disk quota.

Redact with an appropriate external editor, preserve the original privately, and attach the new file with `--derived-from ORIGINAL_SHA256`. Inspect the redacted file. It needs a different hash, per-evidence publication permission and `sensitive_review=approved` before public export. No automatic image redaction.

## Registered sources and import

```sh
python scripts/psf_history.py --history-root /private/psf-history sources add --source-id pilot --type project_folder --location /work/app --scope "*.md" "evidence/*.json"
python scripts/psf_history.py --history-root /private/psf-history sources list
python scripts/psf_history.py --history-root /private/psf-history import --source-id pilot --dry-run
python scripts/psf_history.py --history-root /private/psf-history import --source-id pilot
```

Only registered local paths and selected scopes are scanned. Omit location for `not_configured`; missing/denied paths are blocked, with no substitute project search. Build/dependency directories are skipped. Scopes use `PurePosixPath.match`: basename globs also match nested basenames. Use exact relative paths for a narrow pilot. `issue_pr` requires an authorized local export; it does not fetch URLs.

Structured usage JSON imports deterministically. Markdown/HTML/text and other JSON exports produce reviewable **mention candidates** with hashes and line locators, never automatic successful runs. No conversation or snippet is copied by default. Inspect the original within scope, then create a historical record with its `source_refs`; keep the original `reported_claim` separate. Identical source bytes/locator deduplicate; similar titles/dates do not merge. Registry counters describe the latest scan. Candidates remain separately counted until explicitly reconciled.

For a historical record, the first `source_refs` entry identifies the original execution interval (file hash plus precise lines/message/section); later entries provide context. Reimporting that same first interval under a new UUID still deduplicates. An exact matching mention candidate becomes linked, separate from unresolved candidates; that link alone does not establish activation. Distinct runs need distinct interval locators, not merely the same whole-project report or design source.

`merge private-export.zip` imports revisions/evidence from another collector. `--dry-run` writes nothing, including when simulating a revision chain. Same run/revision/digest is a no-op. Conflicting content/parents go to `quarantine/`. Corrupt/future records are quarantined while other records continue. Unsafe paths/symlinks or limits reject an archive. Public summaries cannot be merged as usage evidence. Source files are never executed or rewritten.

External cases can use the [minimal form](../assets/submission-template.md); no name/email/company is required. Track `collection.review_state`: `received`, `needs_information` or `ready_for_review`, `reviewed`, then `reproduced` or `not_reproduced`. Failed reproduction does not prove a false report. A public issue is already public; private cases belong in an authorized private file/inbox.

## Reports, exports, retention

```sh
python scripts/psf_history.py --history-root /private/psf-history report --project project-alias
python scripts/psf_history.py --history-root /private/psf-history --json report
python scripts/psf_history.py --history-root /private/psf-history rebuild-index
python scripts/psf_history.py --history-root /private/psf-history export
python scripts/psf_history.py --history-root /private/psf-history export --public --run-id UUID
```

Local Markdown/JSON reports show scope/status, activation, lifecycle, project/version/checks, findings, missing evidence and explicit denominators. Unique runs and screen checks are separate, as are live/historical/benchmark records. Mentions and aggregates do not become usage; compare-only defect discovery is not a tool failure. Duration/tokens/cost are observed values only, never missing-as-zero. No overall quality score or causal skill-benefit claim. SQLite is derived and rebuildable from JSON.

Private exports contain full revisions and available evidence, including private free text. Public ZIPs use a strict allowlist: UUID, enum outcomes/activation and explicitly approved redacted evidence. They omit free text, project names, host strings, source paths, URLs and original evidence. The latest record must allow publication and pass sensitive review; included attachments need separate permission/review. Confirm those assertions against the actual conversation. Export creates a local file, not a publication.

`purge --run-id UUID --confirm-run-id UUID` explicitly removes the local run, linked export packages, quarantine branches, receipts containing its ID and derived index/report. A bundle with multiple runs is removed as a whole. Original submissions, sync destinations, backups and third-party copies need separate deletion; no retraction is implied. Retention never triggers autonomous deletion.

Atomic writes and an OS lock preserve previous revisions. Contention returns conflict; retry only the logger. Symlinks/Windows junctions are rejected, but this is not a defense against a concurrent same-machine attacker replacing directories. Keep storage owner-writable. Configure limits at `init`. Unicode paths have Windows execution evidence; Unix execution remains unverified.

Exit codes: **0** handled (including OFF/duplicate), **2** invalid, **3** conflict, **4** blocked/unavailable, **5** partial batch/pending sync. Command success never means an app passed. JSON batch responses give counts and per-item statuses; mutations return the item/digest. Errors omit input contents.
