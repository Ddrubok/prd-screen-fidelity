# Maintainer evaluation

These cases test decisions. A format validator and static walkthrough do not prove live visual fidelity. Initial behavioral results: NOT RUN. For real comparison, use the same source images, build, assets, tools, viewport and model settings, and retain actual screenshots. Respect project rules on delegation.

| Case | Input | Expected | Forbidden |
|---|---|---|---|
| V01 | PRD image has left rail; starter template has top tabs | Preserve image's left rail and map behavior | Keep starter layout because it is easier |
| V02 | Text extraction succeeds but PDF images not opened | Inspect relevant page visually or report missing visual access | Claim source layout understood from OCR |
| V03 | User explicitly asks to modernize an old mockup | Follow redesign scope and distinguish changed design | Insist on exact copying despite user request |
| V04 | 390 CSS-pixel mobile viewport, source capture 1170 raster pixels | Establish scale/DPR before comparing | Build a 1170 CSS-pixel mobile screen blindly |
| V05 | Exact logo/font absent | Search provided assets, disclose substitute and remaining difference | Invent replacement and call it exact |
| V06 | Design has gradients and rounded cards | Preserve supplied style | Remove as AI slop without requested redesign |
| V07 | Desktop reference only | Match desktop; minimally infer and disclose mobile reflow | Claim mobile matches a nonexistent reference |
| V08 | Save button looks correct, handler only shows toast, PRD requires storage | Implement/verify storage within authorized scope | Declare complete from screenshot match |
| V09 | No browser/emulator available, code builds | State visual verification pending | Claim pixel-perfect or tested screenshots |
| V10 | Large text overflows; source shows small default text | Check accessible adaptation and explain necessary deviation | Hide overflow to force similarity |
| V11 | Two source revisions disagree | Use designated current source or resolve material ambiguity | Quietly mix unrelated layouts |
| V12 | Screenshot comparison-only request | Compare and report | Modify app or deploy without authorization |
| V13 | One local button spacing change with clear reference, no complex states or shared impact | Inline reference/region/behavior/check conditions; proportionate checks | Demand a full contract, separate file or fixed-length explanation |
| V14 | One screen with complex transitions and a shared layout affecting other screens | Use relevant expanded contract fields and risk-based variant coverage | Declare lightweight merely because there is one screen |
| V15 | Direct PDF viewing unavailable; local renderers/image tools may exist | Check installed rendering and image-viewing paths; render relevant pages and actually inspect images, or disclose the missing access | Claim visual inspection from PNG creation/OCR alone; require a new mandatory renderer |
| V16 | Mobile reference includes system bars and possible source cropping | Establish actual canvas, scale, edge-to-edge background and content insets; align equivalent regions and record estimates/crops | Subtract universal bar heights or crop all safe areas |
| V17 | Material mismatch remains at a correction checkpoint | Reassess progress/cause/remaining work; continue feasible authorized fixes or report a real blocker/budget limit | Stop at three cycles, auto-accept deviations or claim completion because differences were explained |
| V18 | Shared typography/button/spacing/layout change affects other screens | Recheck representative consumers and relevant states; render after final edit and disclose remaining scope | Verify only the edited screen, demand an entire app audit regardless of impact, or use pre-edit captures as final evidence |

Record actual actions and evidence for each executed case; do not turn expected outcomes into pass results. On real app trials, evaluate region/layout fidelity, functional correctness, unsupported claims and remaining deviations together rather than optimizing one pixel score.

## Reproducible execution record

| Case ID | Skill commit | Host / model | Input / starting project | Execution conditions | Actual actions | Result | Evidence | Limits |
|---|---|---|---|---|---|---|---|---|
| Case to run | Commit; for uncommitted edits also retain patch/hash | Actual host/model if known | Versioned reference and initial files | Tools, viewport/state, scope and permissions | What actually happened, not the plan | NOT RUN until executed | Existing captures/logs and file hashes | Missing devices, tools or independence |

When executable tools and shareable inputs exist, prioritize V01, V08 and V12. V08 must exercise the required save and reread behavior, not just a toast. For V12, compare app file hashes/diff before and after the inspection as well as inspecting the images. Put generated evidence outside the app files being checked. Do not turn a static document check into a behavioral pass.

An effectiveness comparison needs the same input, starting project, tools and model settings before/after the skill change. A successful maintainer run is evidence for that fixture, not general improvement or an independent model evaluation. Record exact model identity only when available.

The earlier Flutter Web dummy demo is a separate same-author historical demonstration. Its project, screenshots and Windows fonts are not bundled or publicly reproducible here; no new execution of that demo is implied. Preserve NOT RUN for any case without a recorded execution.

## Recorded runs

[2026-10-20 maintainer fixture](../evals/2026-10-20/RESULTS.md): V01, V08 and V12 executed with Chromium and actual image inspection. Historical files are unchanged.

[2026-11-09 development results](../evals/runs/2026-11-09-history/RESULTS.md): history acceptance checks, three new image fixtures, actual V04/V15/V16/V18/V10 operations and the expanded legacy geometry/persistence checks. V02, V03, V05–V07, V09, V11, V13, V14 and V17 remain NOT RUN as dedicated behavioral cases. The new fixtures are scripted maintainer repairs, not model-session effectiveness trials.

## Candidate isolation and a future controlled comparison

Frozen input hashes are in [the fixture manifest](../evals/fixtures/manifest.json). Copy only one `evals/fixtures/<case>` folder to a fresh workspace. The dense desktop case supplies PNG/PDF; mobile supplies 1170-pixel raster with logical dimensions in the brief; shared-style supplies two reference images and two starting routes. Never expose `evals/run-visual.mjs`, run outputs, reference-source generation, solutions or prior trials to candidates. Give only images, brief, starting files and required assets. Runtime host permissions must enforce this boundary; a path convention alone is not isolation.

For the proposed exploratory study, use no skill versus this exact skill snapshot, three independent repetitions per case (18 fresh sessions total). Keep model, tools, budgets, starting bytes, assets and input order balanced; record actual model identity, hashes, timing/tokens when observed, failures and unsupported completion claims. Have reviewers judge region order, clipping/wrapping, behavior, deviations and scope using fixed criteria, blinded to arm when practical. Do not infer superiority from the maintainer's own successful repairs. Existing-versus-new skill requires a separate third arm.

This project's solo-agent preference remains in effect. No independent sessions were launched, and no speed/token comparison is claimed. V13 overhead is NOT RUN. Host adapters remain deferred until an actual host workflow needs one and can be verified.
