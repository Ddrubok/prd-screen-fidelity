# Small maintainer fixture

Synthetic, shareable input authored for this run; no production data or external services.

- Reference: `reference.html`, rendered at 960 × 640 logical pixels, DPR 1. The rendered PNG is the visual target for this fixture. Use its left navigation rail, title, form placement, font, spacing and colors.
- Starting app: `start.html`. Its top tabs are a deliberate layout mismatch and its Save handler only changes a message.
- V01/V08 request: implement this reference in `app.html`, preserving the two visible navigation labels and form. Save must store the display name locally on this browser origin and restore it after page reload. No account/server/cross-device storage is required. The second navigation item is a disabled, out-of-scope placeholder; its appearance must remain.
- V12 request: compare the unchanged `start.html` against the reference; report the layout difference without modifying any app/source files. Do not run its Save button for this comparison-only check. Capture evidence separately.
- Conditions: Chromium headless, 960 × 640, DPR 1, English, light scheme, no scroll or browser chrome. No mobile/system bars or custom font files. Use available Arial/sans-serif; record the browser version.

This fixture and implementation share an author and engine. It is not a held-out benchmark, cross-host activation test or proof that the skill improved model behavior. Other evaluation cases remain NOT RUN.
