# PRD Screen Fidelity

[English](README.md) | [한국어](README.ko.md)

**An AI agent skill for implementing or comparing app screens against the visual references in a PRD while checking specified behavior.**

Example screens are treated as the visual specification unless the user identifies them as wireframes, inspiration, or a design to change. The agent inspects source images, maps regions to requirements, implements the interface, and compares actual rendered screenshots against the reference.

This repository is an instruction skill, not a screenshot-to-code application or an automated pixel-perfect guarantee. It works with the agent's available development and browser/device tools.

## Workflow

1. Distinguish implementation, comparison-only and explicitly scoped redesign requests; do not reconfirm clear instructions.
2. View the reference and identify its revision, canvas and UI state. For a small local change, an inline note of the reference, region, behavior and check conditions is enough. Complex states or shared-component changes need relevant parts of the expanded contract even on a single screen.
3. Implement only when requested, preserving the existing stack and designated design. Comparison-only work reports differences without app edits; redesign follows the requested changes and preserves the specified remainder.
4. Render at matching viewport/state and inspect both images. Correct large structural differences before fine details; re-render after the final edit and recheck representative consumers of shared styles.
5. Report visual comparison status separately from visual acceptance and functional results. Keep untested variants, substitutions, remaining differences and blockers visible.

There is no mandatory planning file or full contract table for a small edit. Multiple screens/states can use a short coverage list. A checkpoint after 2–3 correction cycles is not a stopping limit: investigate stalled progress and continue feasible material fixes within scope/budget. Repetition does not turn a mismatch into an approved deviation.

Explicitly requested dummy behavior is valid for a prototype. A production requirement to save data cannot be replaced with a toast just to match a picture.

## Codex, Claude Code, and Gemini CLI

The core uses standard `SKILL.md` frontmatter (name/description), Markdown instructions, and relative references. `agents/openai.yaml` is optional Codex UI metadata, not a dependency of the workflow.

| Host | Personal installation | Invocation |
|---|---|---|
| Codex | Existing supported skill directory; see installation below | `$prd-screen-fidelity` |
| Claude Code | `~/.claude/skills/prd-screen-fidelity` | `/prd-screen-fidelity` |
| Gemini CLI | `~/.gemini/skills/prd-screen-fidelity` | Ask Gemini to activate `prd-screen-fidelity`; inspect with `/skills list` |

Claude Code installation:

```sh
git clone https://github.com/Ddrubok/prd-screen-fidelity.git ~/.claude/skills/prd-screen-fidelity
```

Gemini CLI installation (may ask for installation consent):

```sh
gemini skills install https://github.com/Ddrubok/prd-screen-fidelity --scope user
gemini skills list
```

For a single project use `.claude/skills/prd-screen-fidelity` or Gemini's `--scope workspace`. The `$prd-screen-fidelity` examples below are Codex examples; use Claude's slash command or Gemini's natural-language activation instead. Plain chat websites, Claude uploads, and Antigravity/agy discovery are separate host integrations and are not certified by these CLI checks.

See [compatibility evidence and limits](COMPATIBILITY.md).

## Install

Clone into one skill location recognized by your agent:

```sh
git clone https://github.com/Ddrubok/prd-screen-fidelity.git ~/.agents/skills/prd-screen-fidelity
```

For project-scoped use, use `<project>/.agents/skills/prd-screen-fidelity`. If your host already uses `~/.codex/skills`, that is also the location used in the maintainer's tested setup. Avoid duplicate copies. Refresh/restart the session if the skill does not appear in its selector.

## Use

```text
$prd-screen-fidelity Implement this PRD's example screens and features.
Keep the supplied layout and style. Compare actual app screenshots
with the reference at matching dimensions and correct the differences.
```

```text
$prd-screen-fidelity Compare the current screen with page 6 of this PRD.
Report differences only; do not change the app.
```

Provide the PRD/reference images and project location. Original fonts/assets, target viewport, and state variants improve comparison. Missing materials must be identified rather than silently invented.

## Limits and evidence

- A build passing is not visual verification. If the app cannot run, visual verification remains pending.
- Raster dimensions are not automatically CSS pixels; device scale, cropping, fonts, data, and scroll state matter.
- PDF pages can be rendered with installed tools when direct viewing is unavailable, but generated images must actually be opened. PDF DPI is not app DPR. Compare matching app regions; do not subtract fixed system-bar heights or automatically crop safe areas.
- Pixel differences are supporting evidence, not perceptual similarity or a pass score.
- Compared means both images were inspected, not that the screen passed. A required functional failure prevents overall implementation completion even when the image matches. Unverified final edits remain pending.
- One desktop screen does not establish a mobile design; inferred reflow is disclosed.
- Accessibility and working controls remain required; material conflicts need a specific, minimal resolution.
- Explicit redesign requests override fidelity to the old image. The skill does not remove a supplied style merely because it resembles an AI-generated pattern.

## Local demonstration

A maintainer-created Flutter Web dummy app was implemented from separately authored, frozen HTML/CSS references. Captures at 390×844 and 430×900 were compared, and 18 message-only buttons were checked in Chromium. This was a same-author demonstration, not an independent evaluation of skill effectiveness or a native-device test. The demo, screenshots, and Windows fonts are not bundled in this repository.

A separate [2026-10-20 web fixture](evals/2026-10-20/RESULTS.md) includes its source, captures and execution record: V01 left-rail implementation, V08 save/reload persistence, and V12 comparison-only file preservation were exercised. Other evaluation cases remain NOT RUN. This same-author fixture does not establish a general accuracy improvement or update the historical cross-host compatibility claims.

## Files

- [SKILL.md](SKILL.md): instructions for implementation and verification.
- [agents/openai.yaml](agents/openai.yaml): skill discovery metadata.
- [Screen contract and comparison](references/contract-and-comparison.md): viewport, source, state, and evidence controls.
- [Evaluation cases](references/evaluation.md): 18 maintainer cases and a results format; load only when changing or evaluating the skill, not for ordinary screen work. Execution records distinguish runs from NOT RUN cases.
