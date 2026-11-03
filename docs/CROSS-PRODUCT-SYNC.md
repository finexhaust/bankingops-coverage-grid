# Cross-product context sync — BOCG / FinExhaust / Ficta Meridian

Updated: 2026-11-03. The earlier access blocker below is historical.

The proposed financial-work context is pinned independently from released
coverage and evaluation evidence:

- Context v0.1.0, commit `f1dae918deec1842a908ffa4df0a001f804c749c`.
- 48 retained division keys, five proposed parent domains, nine optional
  capabilities. No catalogue IDs or evidence mappings were retired or promoted.
- FinExhaust commit `f1fcbb6b` integrates the context into new refinery
  preparations, the Workbench reference panel, archive/PDF metadata, Harbor
  exports and both public websites' shared manifests.
- The common reference is presented at
  [FinExhaust BOCG](https://finexhaust.com/bocg/#financial-work).
- Public context bytes and their pin are published under
  `/manifests/financial-work-context.json` and
  `/manifests/financial-work-context-pin.json` on both finexhaust.com and
  fictameridian.com. `/manifests/site-build.json` identifies the current build.
- `scripts/sync_bocg_context.py` and the daily public-release workflow keep
  these projections aligned. The release manifest and context pin remain
  separate: historical evidence is not rebound by context publication.

This is an owner-requested, model-assisted context proposal. It does not claim
independent panel consensus, additional benchmark coverage, new SME approval
or a new model evaluation. BankingEnv/cleanroom execution records retain their
original inputs and versions.

## Historical status — 17 October

Checked: 2026-10-17T02:45Z (UTC)  
Owner signal: **PROCEED** received — Finexhaust still **not** on Cursor App selected-repos (agent re-probed: 404).

## Done

| Surface | Pin | Evidence |
|---|---|---|
| **cleanroom-eval** | `v1.2.0` published | https://github.com/thefazzer/cleanroom-eval/releases/tag/v1.2.0 |
| **BOCG observatory** | on `main` (PRs #36, #37) | `reference/public-eval-observatory.v1.json` · S9-G6 · 4 LLMAJ cases `paint_eligible: 0` |
| **cleanroom companion pin** | `1.2.0` / `github_release_published` | `reference/cleanroom-eval-companion.v1.json` |
| **Finexhaust apply pack** | `integrations/ficta-meridian/` | includes `apply-to-finexhaust.sh` one-shot |
| **BOCG release** | reminting **v0.6.3** on this branch | binds observatory + companion pin into the published manifest |

## Live Meridian (still gap)

| Check | Current |
|---|---|
| URL | https://fictameridian.com/manifests/latest.json |
| `built_at` | `2026-10-16T09:04:40Z` (Finexhaust `c6d7a1c`) |
| `bocg.tag` | `v0.6.2` |
| `cleanroom_eval` | **absent** |
| `public_eval` | **absent** |
| Lab footer | `cleanroom-eval · 2026-09` (not `1.2.0`) |

Daily Finexhaust rebuild is running; the observatory generator / Lab UI pack was never applied.

## Hard blocker (unchanged)

Cursor GitHub App `repository_selection=selected` includes **only** `thefazzer/bankingops-coverage-grid`.

| Target | Result |
|---|---|
| `thefazzer/finexhaust` | **404** — cannot clone, push, or `workflow_dispatch` |
| SSH `172.237.124.65` | **denied** |

## Owner: one command after Finexhaust checkout

```bash
# Finexhaust repo root, with bankingops-coverage-grid as a sibling (or set BOCG_ROOT)
bash ../bankingops-coverage-grid/integrations/ficta-meridian/apply-to-finexhaust.sh
git add ficta-meridian-site && git commit -m "Meridian: cleanroom 1.2.0 pin + LLMAJ observatory" && git push
gh workflow run "Ficta Meridian daily manifest release"
```

Drive mirror of the pack: https://drive.google.com/drive/folders/1hFyuWgb08NbXNdQTX3QtXW8quwQd4oD8

## Acceptance once live

1. `latest.json` → `cleanroom_eval.version == "1.2.0"`
2. `latest.json` → `public_eval.llmaj.cases` length 4, all `paint_eligible: false`
3. Lab footer → `cleanroom-eval · 1.2.0`
4. Lab `#public-eval` names Mercor, Rogo, BankerToolBench as recorded non-paint
