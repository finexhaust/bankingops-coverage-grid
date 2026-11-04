# BOCG regeneration: 19 October 2026

This is a fresh generation using models available from the configured providers on 19 October 2026, Europe/London. It is a **provisional taxonomy with an incomplete independent panel**, not a corroborated finding about banking work or seat economics.

The released matrix has 25 business areas, grouped from 62 admitted labels. Only DeepSeek V4.1 Flash (provider ID `deepseek-flash`) and Qwen 3.8 27B returned three protocol-valid samples. The requirement for at least four independent vendors is **not met**. Kimi K3 supplied two valid samples and MiMo v2.6 Pro one; their other samples put division names before evidence, contrary to I5. Neither family contributes to this release's consensus or seat pools. GLM 5.3 returned transport errors; GPT 6 Astra was unavailable because both configured OpenAI accounts exhausted credit. See [exclusions](exclusions.json), [sample summary](RUN_SUMMARY.json) and [every raw response](runs/efd90b74/).

The [system prompt](system.txt) and [user prompt](prompt.txt) are unchanged. Prompt SHA-256 is recorded in [prompt.sha256](prompt.sha256); rendered year is 2026, seat admission floor USD 200,000. Each model has three planned samples. [Panel parameters](panel.yaml), [provider model listings](provider-models.json), effective request parameters and any provider adaptations are public. Browsing and retrieval are off. No institution holdings were sent to this panel.

The initial panel and MiMo increment completed before response content was inspected or aliases authored. Only interrupted Qwen transport slots were repeated. Successful responses were not rerun to improve agreement. Additional unsuccessful OpenAI attempts, original Qwen errors and exact initial/incremental panels remain in [attempt history](attempt-history/); replacement slots retain the earlier receipt and its hash. [Assembly receipt](generation-receipt.json) records the producer, Prefect run and input hashes.

[Aliases](aliases.yaml) are provisional automated decisions, not human rulings. Composite activity names that cannot be safely narrowed stand alone. The old task-concept ruling is archived under `reference/history/`; new roles and tasks remain AUTO and unreviewed. Old public-eval overlays retain their original catalogue bindings and are historical, not evidence of coverage of this new taxonomy.

The new explicit `eligible-models/v1` policy excludes ineligible models from the consensus denominator and from axis, anchor and seat pools. All attempted model columns remain visible. Historical matrices are unchanged. With two eligible models, Strong means two supporting models and Moderate one. These are agreement labels, not confidence estimates. See [matrix](matrix.csv) and SPEC-01 section 5.

Each area's seat estimate is the median of admitted model claims: annual cost-range midpoint multiplied by the claimed fraction of work with checkable outcomes. The prompt's admission floor biases the pool upwards. It is neither a product price nor measured savings.

Of the [291 anchor/seat rows](corroboration.csv), 31 A1 (regulatory) anchors for the six ISDA-adjacent areas (`repo_secfin_collateral`, `regulatory_reporting_conduct_compliance`, `trade_lifecycle_operations`, `clearing_settlement_custody`, `credit_trading`, `listed_derivatives_client_clearing`) were checked on 4 November 2026 by `claude-fable-5-1` (agent) against the cited source text: eCFR (point-in-time 2026-10-29), the EU Publications Office Cellar Official Journal texts, FINRA, BIS and, for 7 U.S.C. § 2, Cornell LII because uscode.house.gov returned 404. Result: 24 VERIFIED, 4 PARTIAL, 3 REFUTED. The refuted citations are the nonexistent section 17 CFR 23.494, 17 CFR 1.33 misidentified as swap-dealer registration, and MiFIR Article 27 misidentified as best execution. The reserved section 17 CFR 23.1 is PARTIAL, not REFUTED.

A follow-up primary-source check by the OpenAI GPT-6 Astra Pro agent on the same date refuted nine further occurrences of those three incorrect citations. Two EMIR Article 39 notes were corrected to describe their narrow segregation/portability scope; their PARTIAL status was retained. The [follow-up record](../docs/corroboration-follow-up-2026-11-04.md) names the sources and affected rows. Totals are now **24 VERIFIED, 4 PARTIAL, 12 REFUTED and 251 UNVERIFIED**. The 101 unchecked A1 rows and all A2 filings (89), A3 market-size claims (36) and A4 seat claims (25) remain UNVERIFIED. No division is fully corroborated and G6 still fails.

## Reproduce from retained responses

From the repository root, with its Python dependencies installed:

```sh
PYTHONPATH=bocg python -m bocg.cli normalise -w live-run-20261019
PYTHONPATH=bocg python -m bocg.cli matrix -w live-run-20261019
PYTHONPATH=bocg python -m bocg.cli corroborate --ledger live-run-20261019/corroboration.csv -w live-run-20261019
PYTHONPATH=bocg python -m bocg.cli grid -w live-run-20261019
python tools/build_operating_catalogue.py
python tools/build_task_concepts.py
PYTHONPATH=bocg python -m bocg.cli gate all -w live-run-20261019
```

`reference/taxonomy-source.json` selects this run. Use Finexhaust's generation, retry and assembly flows to create another run; do not overwrite this one. The generation receipt pins the original generation code separately from later normalisation and catalogue code. The release manifest pins all published evidence.

The initial regeneration did not run the test or gate suites. On 4 November 2026 the full generation gate suite was executed against the retained responses and current ledger. G1–G5 and G7–G9 passed; G6 (corroboration) and G10 (independent panel) failed. The command therefore exits non-zero. [gates_report.json](gates_report.json) records the actual results and per-gate evidence instead of the former NOT_RUN placeholders. G9 uses the companion replay repair: the original eligibility-policy bytes are carried into the temporary replay before normalisation, and both the CSV and JSON matrices reproduce. No source response, matrix, exclusion policy or admission result was changed to obtain these results. G6 and G10 still require additional evidence.
