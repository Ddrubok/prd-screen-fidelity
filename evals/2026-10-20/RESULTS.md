# Maintainer run — 2026-10-20

This is a real browser exercise on a small synthetic fixture, performed by the same Codex maintainer who authored the reference and implementation. It is not an independent agent evaluation or a before/after effectiveness comparison. The exact backend model identifier was not available and is not inferred from a role label.

Skill revision: uncommitted changes on base `8ac98fa`. Exact SKILL.md and comparison-guide SHA-256 values are recorded in [run-results.json](run-results.json). The fixture input/start hashes are in [reference-run.json](reference-run.json); the same hashes are preserved in the later run. No new skill commit is claimed.

| Case ID | Skill commit | Host / model | Input / starting project | Execution conditions | Actual actions | Result | Evidence | Limits |
|---|---|---|---|---|---|---|---|---|
| V01 | 8ac98fa + recorded uncommitted skill hashes | Codex maintainer session; model ID unrecorded | brief.md, reference.html, start.html | Windows; Node v22.18.0; Chromium 153.0.8010.12; 960×640; DPR 1 | Captured/opened reference and starting screen; changed top tabs to left rail in app.html; rendered after final edit; opened final image | Criterion met for this fixture: left rail and initial form layout match the inspected reference | reference.png, start.png, final.png; navigation bounds in run-results.json | Same author/engine; one desktop state; not a general visual accuracy result |
| V08 | Same | Same | Brief requires same-origin local storage after reload | Fresh browser context; no preloaded saved value or external service | Entered Reopened Name, clicked Save, reloaded and reread input/localStorage; opened a second page and reread; opened post-reload capture | Criterion met: value persisted across reload and another page on the same origin | saved-after-reload.png; assertions in run.mjs and run-results.json | No server, cross-device, browser-restart or failure-injection test; these were not required by this fixture |
| V12 | Same | Same | Compare start.html against reference; no app edits allowed | Separate comparison step, image/geometry reads only; no Save click | Opened comparison-only.png and reported top-tabs mismatch; compared all fixture HTML hashes before/after the browser run | Comparison delivered; app still needs visual correction; source files unchanged | comparison-only.png; matching startingHashes/endingHashes in run-results.json | Hash scope is reference.html, start.html and app.html; screenshots/JSON were generated separately |

## Visual inspection record

The maintainer opened the reference and starting PNGs before implementing app.html, then opened final.png, saved-after-reload.png and comparison-only.png after the browser run. PNG creation alone was not counted as inspection.

- Reference vs starting: reference navigation is a 208×640 left rail. Starting navigation is a 960×75 top bar; it shifts the heading/form left and down. This is an unapproved structural difference, not an accepted deviation.
- Reference vs final: the left rail, selected navigation item, title, supporting text, label, input, Save button, spacing and visible colors align in the inspected 960×640 initial state. No material unexplained discrepancy was observed in that state. No similarity percentage is claimed.
- Saved state: the reopened input shows `Reopened Name`. The screenshot supports the visible state; persistence is supported by the actual save/reload and new-page checks, not by the screenshot alone.
- Comparison-only target: visual verification **compared**, visual outcome **needs correction**, functional outcome **not verified in this comparison-only step**. Completing the comparison report does not mean the starting app is complete.
- Implemented target: visual verification **compared**, visual outcome **meets fixture requirements** for the initial reference state; required save behavior **passed** in the recorded scope. The saved-name state is a behavioral variant, not a separately supplied design. Disabled Notifications is explicitly out of scope in the fixture brief.

Other cases V02–V07, V09–V11 and V13–V18: **NOT RUN** as behavioral evaluations. Their document rules were reviewed, which is not a behavioral pass. In particular, no PDF rendering, real mobile safe-area or shared-component regression trial was performed. Historical host compatibility and the unbundled Flutter demo retain their original limits.

## Reproduce the tool checks

Use existing Node.js and Playwright/Chromium. These are optional maintainer tools, not runtime dependencies of the skill. If Playwright is not resolvable from this folder, point `PLAYWRIGHT_MODULE` to an existing installation's `index.mjs`.

```powershell
$env:PLAYWRIGHT_MODULE = 'C:\path\to\existing\node_modules\playwright\index.mjs'
node .\evals\2026-10-20\run.mjs reference
node .\evals\2026-10-20\run.mjs check
```

The script serves only the fixture HTML over loopback on a temporary port, uses a new headless context, clears its synthetic stored value and closes the browser/server. It writes captures and JSON in this fixture directory, replacing prior run artifacts there. Preserve this recorded evidence before running again. Open both reference and actual images yourself; assertions do not perform visual inspection. Reproducing the runner tests the supplied implementation, not another model's ability to implement it from scratch.
