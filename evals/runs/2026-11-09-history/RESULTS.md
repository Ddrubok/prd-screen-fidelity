# Development and validation: 2026-11-09

[English](RESULTS.md) | [한국어](RESULTS.ko.md)

Baseline: `344a958add4ccadb96200042b7cf55aa9c8ed503`. Version: `2026.11.09-history.1`; schema version: `1.0`. This records development checks performed before publication; publishing these artifacts does not establish skill effectiveness. Exact tested code hashes and named results are in [run-results.json](run-results.json); instruction hashes are in [implementation-manifest.json](implementation-manifest.json). The [illustrated walkthrough](../../../README.md#visual-examples) shows the reference, before/after and additional checked states.

## Delivered scope

Phases A–D are implemented: schemas/example, optional stdlib CLI, immutable revisions, conservative outcome validation, scoped historical candidates, deduplication/quarantine, private directory sync, reports, reviewed public summaries, index reconstruction and explicit purge. Optional wrapper/attachment commands also work. The skill adds only a short history-policy link and preserves visual/functional verification. English is the main documentation language; Korean README and this result are separate.

Changed entrypoints: [SKILL.md](../../../SKILL.md), [history CLI](../../../scripts/psf_history.py), [usage guide](../../../references/usage-history.md), [record schema](../../../schemas/usage-record.schema.json), [registry schema](../../../schemas/source-registry.schema.json), [tests](../../../tests/history/test_history.py). Reference and evaluation guidance, README files, compatibility metadata and Codex display text were updated. Original `evals/2026-10-20` files remain unchanged.

## History checks

**34 tests executed, 34 passed**, Python 3.12.10 on Windows. Both JSON Schemas and the synthetic example also passed independent Draft 2020-12 validation; the skill-creator validator passed. These developer checks use optional local validators; the runtime collector depends only on Python's standard library.

```sh
python -m unittest discover -s tests/history -v
python scripts/psf_history.py --history-root /private/psf-history init --mode local
python scripts/psf_history.py --history-root /private/psf-history --json start --project example --task compare
python scripts/psf_history.py --history-root /private/psf-history report
```

| Plan case | Executed evidence and limit |
|---|---|
| H01 | Repeated ZIP import retains count/file set; same source interval/new UUID deduplicates |
| H02 | Same revision/different content quarantined; original retained |
| H03 | Sibling branches retained; two concurrent CLI writers produce stored/conflict with both inputs preserved |
| H04 | Start remains started/unknown without an end |
| H05 | Historical version/commit remain null |
| H06 | Name mention becomes a review candidate, not usage; exact-interval reconciliation is separate |
| H07 | Success claim without captures stays unverified |
| H08 | Compare/history/report operations preserve app and installed instruction bytes |
| H09 | Required save failure rejects implementation completion |
| H10 | Inferred screen excluded from supplied-reference matches |
| H11 | Capture predating the final edit cannot certify completion |
| H12 | Changed evidence hash detected; finish rechecks current local bytes |
| H13 | Deleted local evidence detected; external link stays unchecked. Actual link expiry probe NOT RUN |
| H14 | Corrupt/future-schema records quarantined; valid batch items continue |
| H15 | ZIP traversal/absolute paths/ZIP symlinks and native filesystem symlinks rejected on Windows |
| H16 | Report-embedded commands stay inert |
| H17 | Public-review gate enforced; free text, paths and private URLs absent from allowlisted summary |
| H18 | Unavailable destination simulated; local records survive and retry deduplicates. Live network disconnect NOT RUN |
| H19 | Injected atomic-replace failure preserves previous revision; forcibly exited process releases lock. Mid-write power-loss durability NOT RUN |
| H20 | Korean/space paths passed on Windows. Unix NOT RUN |
| H21 | Deleting/rebuilding SQLite reproduces rows and aggregates |
| H22 | Date-only stays a date; invented midnight rejected |
| H23 | Redacted attachment has a new hash and preserved lineage; reviewed derivative exported |
| H24 | Compare delivery complete and visual needs-correction coexist |
| H25 | Unknowns, record kinds and denominators retained; missing costs not zero |
| H26 | OFF creates no run and still executes the explicit product command. Missing-tool model behavior NOT RUN |

Additional checks cover public/private lifecycle boundaries, source reconciliation, purge of local derived copies, dry-run chains and wrapper exit 0 without acceptance. Test counts describe checks, not product quality or skill effectiveness.

## Actual collection pilot

One known local project, four explicitly selected documentation/result files, one registered source checked. Source bytes remained unchanged. No name mention/load log in that selected scope established actual activation. One historical aggregate was manually attributed to those files with unknown occurrence/version/model and unverified outcomes. It contributes **zero usage records**, rather than inventing an execution count. No captures or full conversation were copied. Private records/report remain outside this repository under the user's history directory; only these aggregate collection facts are described here. No other projects or host-private databases were scanned. This is not a complete history census.

## Visual exercises

The three frozen [candidate fixture folders](../../fixtures/manifest.json) cover dense desktop, Korean/Japanese mobile text, and two consumers of shared styles. Chromium 153.0.8010.12 / Node 22.18.0 exercised geometry and persistence. [Latest machine record](../2026-11-09-visual-03/run-results.json) and [separate image review](../2026-11-09-visual-03/image-review.json) retain different evidence levels.

| Case | Actual result |
|---|---|
| V04 | 390×844 logical viewport / DPR 3 / 1170×2532 raster checked; source and final image inspected |
| V15 | One-page input PDF rasterized with pypdfium2 5.15.1 at 96 DPI to 1100×720 and opened; table/header/layout visible. PDF antialiasing differs from Chromium; no pixel-perfect claim |
| V16 | Synthetic top 44/bottom 34 CSS-pixel regions and matching app crop inspected; these are fixture-specific dimensions, not real-device measurements |
| V18 | Profile and notifications re-rendered after shared style repair; both reference/final views inspected and both save/reload flows passed |
| V10 | 200% text wrapping and scroll reachability checked. Initial image review found a fixed inset covering the button; scroll container repair and scrolled-button capture verified access afterward |
| V01/V08/V12 | Existing fixture rechecked in a new output folder; title/input/button/main bounds added to navigation; persistence and unchanged original HTML checked |

The first authoring run's mechanical V10 result missed the inset overlap visible in its image. Its result is superseded by the later image review and repaired fixture. Run `visual-02` added scroll checks; `visual-03` also restored matching input state after persistence testing and verified frozen input hashes. Prior files were retained; no old pass was silently substituted. The candidate inputs were frozen after these authoring refinements.

To repeat maintainer checks with an existing Playwright installation:

```sh
node evals/run-visual.mjs evals/runs/NEW_RUN_ID
```

Set `PLAYWRIGHT_MODULE` to an existing `playwright/index.mjs` if normal package lookup cannot find it. The runner rejects an existing result directory and verifies frozen inputs. PDF rasterization and actual image opening remain separate steps; its pending V15/image-review fields must not be treated as passes. Optional renderer example, with pypdfium2 already installed:

```python
import pypdfium2 as pdfium
with pdfium.PdfDocument("evals/fixtures/dense-desktop/reference.pdf") as doc:
    page = doc[0]
    page.render(scale=96 / 72).to_pil().save("evals/runs/NEW_RUN_ID/pdf-page-1.png")
    page.close()
```

These repairs were scripted by the same author who made the references; they test fixture behavior and inspection procedures, not autonomous model quality. V13 overhead and the proposed **18 independent model sessions are NOT RUN** under the workspace's solo-agent setting. No speed/token advantage is claimed. Native-device and authenticated cross-host logging remain NOT RUN; phase F adapters are deferred. Stored assertions are not tamper-proof attestations, the wrapper is not a sandbox, and the private store assumes owner-controlled access.
