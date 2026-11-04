# A1 corroboration follow-up — 4 November 2026

Scope: the `live-run-20261019` ledger following the 31-row A1 check in PR #47
at `68805171d2d82708f011ea5ee7991fe2d3cd3fc9`. This follow-up changes no
elicitation prompt, raw response, alias, matrix, taxonomy key or admission rule.
It does not declare a release or satisfy G6/G10.

## Results

The original check by `claude-fable-5-1` (agent) produced 24 VERIFIED, 4 PARTIAL
and 3 REFUTED rows. Those statuses are retained. The OpenAI GPT-6 Astra Pro
agent checked primary sources and marked nine additional occurrences of the
same incorrect citations REFUTED. Every affected ledger row identifies the
checker, check time, source and reason. No row was newly marked VERIFIED.

| Anchor type | VERIFIED | PARTIAL | REFUTED | UNVERIFIED | Total |
|---|---:|---:|---:|---:|---:|
| A1 regulatory | 24 | 4 | 12 | 101 | 141 |
| A2 filing/segment | 0 | 0 | 0 | 89 | 89 |
| A3 market size | 0 | 0 | 0 | 36 | 36 |
| A4 seat/terminality | 0 | 0 | 0 | 25 | 25 |
| Total | 24 | 4 | 12 | 251 | 291 |

These are ledger rows, not distinct regulations. Zero of the 25 divisions
is fully corroborated. Refuted citations are not replaced with more plausible
citations: the emitted claim remains visible and its rejection is recorded.

## Primary-source checks

| Claim | Source read on 4 November 2026 | Finding and action |
|---|---|---|
| 17 CFR 23.494 is a swap-clearing rule | [eCFR Part 23](https://www.ecfr.gov/current/title-17/chapter-I/part-23), displayed current through 2 November 2026; corroborating [2025 GPO Part 23](https://www.govinfo.gov/content/pkg/CFR-2025-title17-vol1/pdf/CFR-2025-title17-vol1-part23.pdf) | No section 23.494 appears in Part 23. Three additional identical claims refuted. |
| 17 CFR 1.33 is swap-dealer registration | [2025 GPO section 1.33](https://www.govinfo.gov/content/pkg/CFR-2025-title17-vol1/pdf/CFR-2025-title17-vol1-sec1-33.pdf) and [CFTC guidance](https://www.cftc.gov/About/CFTCOrganization/MPDSubmitPetitionRegulation30_10) | The provision concerns FCM customer statements. Two additional identical claims refuted. The GPO edition date is retained; no 2026 point-in-time GPO text is claimed. |
| MiFIR Article 27 is best execution | [ESMA MiFIR Article 27](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mifir/article-27-obligation-supply-financial) | The provision concerns financial-instrument reference data. Four additional identical claims refuted. This does not alter the separately cited MiFID II directive. |
| 17 CFR 23.1 | [eCFR Part 23](https://www.ecfr.gov/current/title-17/chapter-I/part-23) | Sections 23.1–23.20 are reserved. The existing PARTIAL classification is retained; it is not counted as VERIFIED. |
| EMIR Article 39 in the reporting/compliance and lifecycle divisions | [ESMA Article 39](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/emir/article-39-segregation-and-portability-0) | CCP and clearing-member segregation/portability obligations substantiate only a narrower activity. The wording that it is not a conduct rule was too broad; both notes are corrected and PARTIAL is retained. Original check attribution remains in each note. |

Fresh retrieval of the eCFR point-in-time API and the current section 38.1
page was unavailable. The existing section 38.1 PARTIAL record and its original
source attribution are retained without a new verification claim. EUR-Lex
returned an access challenge; the accessible ESMA rulebook supplied the EU
checks above. No failed retrieval is treated as evidence of legal absence.

## Nine additional refutations

| Incorrect citation | Additional division rows |
|---|---|
| 17 CFR 23.494 | `commodities_trading`, `fx_cross_asset_combined`, `rates_trading` |
| 17 CFR 1.33 as swap-dealer registration | `commodities_trading`, `rates_fx_combined` |
| Regulation (EU) 600/2014 Article 27 as best execution | `buyside_trading_execution`, `equities_trading`, `fx_trading`, `rates_trading` |

## Remaining qualification work

G6 requires at least two VERIFIED types among A1–A3 for each admitted division,
a VERIFIED A4 claim and no remaining UNVERIFIED or missing rows. The 101 A1,
89 A2, 36 A3 and 25 A4 unchecked rows therefore remain explicit work. The four
PARTIAL rows do not count as VERIFIED. A2 checks require the named filing,
year and printed line item; A3 checks require the named dated series and value.
A4 requires both compensation evidence and a named practitioner judgement that
at least three terminal tasks are record-checkable. Agent source review cannot
substitute for that practitioner requirement.

G10 still has only two eligible independent families. Its four-vendor,
three-valid-sample minimum remains unchanged. No new model call was made and
no historical response was repaired, replaced or retrospectively relabelled.

The full generation gate suite was executed against this ledger at
2026-11-04T04:45:14.959535Z. G1–G5 and G7–G9 passed; G6 and G10 failed.
The generated report contains actual evidence rather than NOT_RUN placeholders.
The corroboration summary and grid are rebuilt from the ledger.

The first execution exposed a G9 replay defect: the temporary workspace omitted
the recorded `exclusions.json` policy, so replay used a different consensus
denominator. A controlled probe reproduced the original matrix when those
unchanged bytes were carried into replay before normalisation. The final run
used the companion G9 repair, which validates and copies that policy and checks
both matrix CSV and JSON. The gate implementation used for this run has SHA-256
`09915e4fd7823d25bbd8741226f6305ed555533ef8f31d05c7868f70e6359f04`.
The unchanged policy hash is
`e138d168097fbe5aa653de7c1b790f47aa0e4b6139b9f84b8ff7d4f730d5a7a6`;
the original and replay CSV hashes both equal
`b6d24730a28f50759847034d5b106ec4aee63196af534c41aaeb867049f842f5`.
No retained input, admission outcome or matrix was edited to make G9 pass.
