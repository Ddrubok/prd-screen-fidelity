# Screen contract and visual comparison

## Minimal contract

Store a small contract in the existing project design/implementation notes when useful. Do not require a new planning system. Use stable IDs so later edits remain tied to the same screen.

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

## Comparison controls

1. Identify source canvas/crop. Raster pixel dimensions are not automatically CSS pixels; verify device scale or record the assumed mapping. Do not stretch the implementation image to conceal a geometry mismatch.
2. Match viewport, orientation, zoom, content, locale, theme, scroll offset and state. Wait for fonts/assets and relevant requests. Use deterministic synthetic data where permitted. Capture each variant separately.
3. Reference images embedded in PDFs may be compressed or scaled. Prefer original design assets when available. Record extraction limitations instead of treating compression artifacts as intended styling.
4. Inspect source and actual screenshots. Check region coordinates, bounding boxes, alignment, wrapping, image aspect/crop, selected state, visible controls and overflow. Match geometry before fine decoration.
5. If using pixel differences, align the same canvas and record the method. Mask only justified variable regions (clock, caret, intentional animation), list them, and do not hide product defects. Font rendering and device differences can cause noise. A low difference score does not establish functional correctness or accessible interaction.
6. Keep a short discrepancy list: `id, screen, source_region, observed_difference, impact, correction, status, evidence`. Classify status as corrected, accepted deviation, pending, or not verifiable. Accepted deviations require actual user/project authority, not a label invented by the implementer.
7. Recheck the original target viewport after responsive changes, and test real interactions after visual edits. Maintain content overflow, text scaling and keyboard access; do not solve visual comparison by clipping real content.

## Evidence levels

- Compared: both reference and actual rendered screen inspected with capture conditions recorded.
- Estimated: inferred measurement or missing design variant; not a source fact.
- Substituted: missing original asset/font replaced temporarily; identify the replacement.
- Not verified: unavailable runtime/device/source or untested state.

Report only the variants actually examined. Screenshots demonstrate the captured state, not every scroll position, device or interaction. Preserve original references; comparisons and annotations belong in separate artifacts.
