# Screen contract and visual comparison

## Choose the record by risk

For a localized change with a clear reference and no complex state transitions or broad shared-component impact, an inline note is enough: reference screen, changed region, related behavior and check conditions. Example: “REF-2, Save button label spacing; retain save-on-click; check the supplied viewport and keyboard focus.” Do not require a separate file, the table below or a fixed amount of user-facing explanation.

Use an expanded record for multiple screens, a complex single screen, multiple states/sizes, conflicting source revisions or shared-component changes. Use only relevant fields in the project's existing notes; screen count alone does not determine risk. Use stable screen IDs. This is not a new planning system.

| Field | Record |
|---|---|
| Source | File, page/frame, revision, screenshot/image ID |
| Screen/state | Route or app screen; signed-in/loading/empty/populated state |
| Canvas | Image dimensions, content crop, known viewport, scale/DPR if known |
| Regions | Navigation, header, body, footer; order and alignment |
| Tokens | Font, size/weight/line-height, colors, spacing, radii; measured versus inferred |
| Assets | Provided filenames, crops, icons, font availability, temporary substitutions |
| Behavior | Region/control mapped to requirement ID and expected effect |
| Variants | Supplied mobile/desktop and interaction states; inferred states separately |
| Open points | Conflicts, missing assets, unknown dimensions, owner decision if needed |

Example: REF-03, PRD page 6, search results, desktop target. Left filters remain a left rail; title remains above results; three columns appear only if shown/required at the target width. Search input maps to R-SEARCH-01. Filter changes update actual results. Do not replace the rail with a top toolbar because a starter template uses one. A spinner not shown in REF-03 may be a justified inferred loading state, not evidence of a new design requirement.

## Screen/state coverage when needed

For several screens or states, keep a short list. Prioritize requested variants and high-risk changes, not every possible device/state combination. These are example records, not executed checks:

| Screen ID | State / size | Reference | Implementation | Visual verification | Functional verification | Remaining differences |
|---|---|---|---|---|---|---|
| SEARCH | Results / supplied desktop size | Provided REF-03, revision 2 | Not started | Not verified | Not verified | Not assessed |
| SEARCH | Loading / same size | Inferred from REF-03; no supplied state design | Not started | Not verified; no direct reference match available | Not verified | Inference needs disclosure |

Implementation, visual comparison and functional checks are independent. Add outcome detail below the row when needed rather than forcing a wide matrix for a small change. Keep untested variants visible.

## PDF visual access fallback

If the host cannot open a PDF visually, render only the relevant pages with an installed local tool. For page 6 using Poppler:

```sh
pdftoppm -f 6 -l 6 -singlefile -r 150 -png "input.pdf" "reference-page-6"
```

If Poppler is absent, check already-installed PyMuPDF, pypdfium2 or another suitable renderer. No particular renderer is a mandatory skill dependency. Open the generated image with an actual image-viewing tool: a PNG being created is not evidence that its contents were inspected. Record the page and rendering conditions. PDF rendering DPI is neither app DPR nor proof of the original logical screen size. If image access remains unavailable, state why and which visual checks remain unverified; extracted text can support requirements discovery only.

## Canvas, system UI and safe areas

Distinguish the full raster dimensions; device frame, document margins and browser UI; actual app/web comparison region; logical viewport and scale; and system bars, notch, keyboard and safe-area insets. Record whether the app background draws behind system bars (edge-to-edge) and where meaningful content is inset. The full app background and safe content area are not the same rectangle.

Use actual device, orientation, capture method, app configuration and measurements. Do not subtract a universal status-bar or bottom-inset height, and do not automatically crop away safe areas. A source may already be cropped or resized. Record unknown or estimated scale, all crop boundaries and excluded regions; align source and actual captures to the same extent without stretching away real differences. If that mapping cannot be established, limit the conclusions accordingly.

## Comparison controls

1. Identify source canvas/crop. Raster pixel dimensions are not automatically CSS pixels; verify device scale or record the assumed mapping. Do not stretch the implementation image to conceal a geometry mismatch.
2. Match viewport, orientation, zoom, content, locale, theme, scroll offset and state. Wait for fonts/assets and relevant requests. Use deterministic synthetic data where permitted. Capture each variant separately.
3. Reference images embedded in PDFs may be compressed or scaled. Use the visual fallback above when necessary and prefer original design assets when available. Record extraction limitations instead of treating compression artifacts as intended styling.
4. Inspect source and actual screenshots. Check region coordinates, bounding boxes, alignment, wrapping, image aspect/crop, selected state, visible controls and overflow. Match geometry before fine decoration.
5. If using pixel differences, align the same canvas and record the method. Mask only justified variable regions (clock, caret, intentional animation), list them, and do not hide product defects. Font rendering and device differences can cause noise. A low difference score does not establish functional correctness or accessible interaction.
6. Record discrepancies when they are found: `id, screen, source_region, observed_difference, impact, correction, status, evidence`. Do not fill an empty discrepancy table before implementation. Use corrected, accepted deviation, pending, or not verifiable. Corrected requires a post-edit check; accepted deviation requires a cited user instruction or project criterion, not elapsed effort or an explanation of the difference.
7. Recheck the original target viewport after responsive changes, and test real interactions after visual edits. Shared font, button, spacing-token or layout edits require representative consumer screens and relevant states to be rechecked, in proportion to their impact; report which were checked and what remains untested. Maintain content overflow, text scaling and keyboard access; do not solve visual comparison by clipping real content.

## Correction loop and stopping

For authorized changes, first correct missing regions, wrong order, canvas/viewport and large sizing differences. Then address typography, wrapping, spacing, assets and surface details. Comparison-only work reports these differences without performing corrections.

One sufficient comparison is enough. After 2–3 correction cycles, inspect remaining differences, improvement trend, likely causes and remaining effort. After two consecutive cycles without material improvement, revisit source quality, font availability, environment and measurement conditions instead of retrying the same edit. Neither checkpoint is an automatic stopping rule. Continue feasible material corrections within scope and agreed budget. Do not invent a budget to abandon fixable work.

If tools, source materials, environment or an agreed budget prevent completion, report the blocker and unresolved differences. Reaching an iteration count does not authorize deviations. Re-render after the final code edit and inspect that final state; otherwise mark it “post-edit verification pending.” Prior screenshots do not verify later edits.

## Evidence levels

- Compared: both reference and actual rendered screen inspected with capture conditions recorded. This describes the comparison action, not a passing result.
- Estimated: inferred measurement or missing design variant; not a source fact.
- Substituted: missing original asset/font replaced temporarily; identify the replacement.
- Not verified: unavailable runtime/device/source or untested state.

Report only the variants actually examined. Screenshots demonstrate the captured state, not every scroll position, device or interaction. Preserve original references; comparisons and annotations belong in separate artifacts.

## Outcome, separate from evidence level

For the relevant scope, report:

- Visual verification: compared / not verified.
- Visual outcome: meets requirements / authorized deviations / needs correction; undetermined when unverified. Record the authority for deviations. Any remaining unapproved material mismatch still needs correction.
- Functional outcome: passed / failed / not verified / not applicable, with actual checks or the reason for non-applicability. “Not requested to execute” usually means not verified, not not applicable.
- Remaining differences, supporting evidence and untested scope.

Visual agreement cannot compensate for a failed required feature. Explaining a difference is not fixing or approving it; an inferred variant is not a match to a supplied design. Do not infer acceptance from an arbitrary similarity score or present blocked/partial work as full implementation completion. A comparison-only report can be delivered completely while correctly finding the app needs correction.

For recorded findings, use `blocking` (required flow unusable), `major` (material layout/content mismatch), `minor` (localized non-material difference), or `rendering_noise` (environment/antialiasing variation). Record the observed difference separately from a cause hypothesis. `fixed_verified` needs post-edit evidence; `authorized_deviation` needs a specific actual user/project authority reference. Do not merge same-looking symptoms without evidence of a common cause.

Aggregate conservatively: one required save failure makes the functional result failed even if other checks passed; passing plus pending checks is partial. A screen needing correction keeps the aggregate visual result at needs correction. A compared desktop screen plus an unverified mobile state is partial coverage, and an inferred mobile layout is excluded from supplied-reference matches. Comparison report delivery can be complete with these defects; implementation delivery cannot. For optional machine-readable records, use [usage history](usage-history.md), keeping record validity distinct from these outcomes.
