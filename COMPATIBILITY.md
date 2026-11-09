# Compatibility evidence

Historical host checks on 2026-10-07. This record concerns `prd-screen-fidelity`; the original discovery exercise also included `app-qa-human`. It was not a separate single-skill activation benchmark. The dates and versions below have not been refreshed by the documentation update.

| Host | Evidence | Limit |
|---|---|---|
| Codex | prd-screen-fidelity was among the installed skills discovered in the maintainer session; structural validator passed | Discovery/structure do not establish every execution stage or support for every host version |
| Claude Code 2.1.107 | Local CLI version/help checked; frontmatter, relative references, installation and slash invocation reviewed against official documentation | No authenticated skill activation or task run performed |
| Gemini CLI 0.59.0 | prd-screen-fidelity was copied with app-qa-human into a test workspace's .gemini/skills and listed as Enabled by gemini skills list | Discovery only; no model inference, activation or task-quality test |

Gemini's existing Unity MCP endpoint was offline during that discovery exercise. It did not prevent prd-screen-fidelity from being listed. This skill does not require Unity MCP, a particular model/provider, paid API credentials, or an orchestration runner. Available development, browser/device and image tools determine actual coverage.

## What each stage establishes

| Stage | Evidence in the historical host checks |
|---|---|
| Installation / discovery | Codex discovery and Gemini test-workspace listing above; Claude installation/invocation instructions were reviewed, not authenticated activation |
| Activation | No dedicated per-host activation result recorded; Gemini's Enabled listing is not model activation |
| Reference document / image access | Relative references were reviewed; no per-host runtime document/image-access trial recorded |
| Actual implementation / comparison | No such trial in the host compatibility exercise. The separate same-author Flutter Web demonstration described in the README is not an independent cross-host test, and its artifacts are not bundled |

Later maintainer fixture runs, if recorded in [evaluation](references/evaluation.md), retain their own dates, environment and limits. They do not retroactively upgrade these historical host checks.

## Host-neutral execution

Read references relative to the installed SKILL.md directory, not the project working directory. Use the host's own file, image, browser and shell tools. If a capability is unavailable, report the missing verification rather than claiming execution. Optional Codex UI metadata does not change the core instructions. A discovered skill is not a successfully executed review.

## Optional history CLI: 2026-11-09

Python 3.12.10 on Windows executed the standard-library history checks, including Korean/space paths, native symlink rejection, concurrent writers, process termination/lock release, mounted-directory outage simulation and index reconstruction. Python 3.10+ is the implementation target; other Python versions and Unix execution have not been certified. The collector uses no host-private database or hook API. Manual invocation/wrapper support does not establish automatic logging in Codex, Claude, Gemini or Antigravity.

The separate browser fixture ran Chromium 153.0.8010.12 through existing Playwright, with PNG viewing and pypdfium2 5.15.1 PDF rasterization. These optional evaluation dependencies are not dependencies of the history CLI. Synthetic mobile insets do not establish physical-device behavior. No new authenticated cross-host activation trial was performed. See [dated results](evals/runs/2026-11-09-history/RESULTS.md).

## Historical official sources

- [Claude Code skills](https://code.claude.com/docs/en/skills): SKILL.md, personal/project directories and slash invocation.
- [Gemini CLI skill management](https://geminicli.com/docs/cli/using-agent-skills/): installation, discovery and activation management.

These checks concern Claude Code and Gemini CLI. Gemini web/Gems, Claude web uploads and Antigravity/agy have separate installation and tool capabilities; support is not implied by model family. No hosted services or account settings were changed.
