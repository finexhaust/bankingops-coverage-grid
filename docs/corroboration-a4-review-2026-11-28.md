# A4 practitioner review - 28 November 2026

Scope: the A4 (seat cost and terminality) rows of seven areas in
`live-run-20261019/corroboration.csv`. This review changes no elicitation prompt,
raw response, alias, matrix, taxonomy key or admission rule. It does not declare
a release or satisfy G6 or G10.

## Method

SPEC-01 section 6: A4 is VERIFIED when the compensation range overlaps a named
survey or filing and at least three terminality tasks are judged record-checkable
by a practitioner reviewer whose id is logged.

- Tasks. The owner, Paul Farrington, acted as the named practitioner reviewer and
  gave a YES, NO or UNSURE verdict on every pooled terminality task of the seven
  areas, as the eligible models worded them. Only YES counts. The reviewer is also
  the publisher of this grid; that is recorded here so a reader can weigh it.
- Cost. An agent computed compensation expense per employee from the filing each
  claim names and tested whether it falls inside that claim's range. A range that
  does not contain the figure from its own named source is not counted, even when
  another source would fit. Paywalled surveys were not checked. Compensation per
  employee is a floor for fully loaded seat cost, not a measure of it, so this is
  a weak test; it shows the claimed range is not detached from the cited filing.

A row that meets one half only is PARTIAL, which does not count toward G6. No row
was marked REFUTED.

## Results

| Area | A4 status | Finding |
| --- | --- | --- |
| `clearing_settlement_custody` | VERIFIED | Tasks: practitioner judged all 3 record-checkable (reconcile custody to subcustodian; settle a trade; update custody safekeeping record). Cost: claimed range USD 150k-300k names the JPMorgan Chase 2024 Form 10-K bank-wide figure. JPMorgan Chase 2024 Form 10-K: compensation expense 51,357 (p.62) over 317,233 employees (p.50) is about USD 162k per employee; Commercial & Investment Bank 18,191 (p.77) over 93,231 (p.80) is about USD 195k. The bank-wide figure falls inside the claimed range. Compensation expense per employee is a floor for fully loaded seat cost, not a measure of it. |
| `repo_secfin_collateral` | VERIFIED | Tasks: practitioner judged 8 of 11 record-checkable; UNSURE on "Execute repo trade", "Process repo settlement" and "Revalue repo book". Cost: the claimed range USD 220k-450k names Goldman Sachs 2024 compensation and benefits over headcount. Goldman Sachs full year 2024 earnings release (15 Jan 2025): compensation and benefits 16,706 over headcount 46,500 is about USD 359k per head. That falls inside the claimed range. The claim of USD 250k-450k naming the JPMorgan 2024 CIB figure (about USD 195k) does not overlap; the Options Group report cited by a third claim is paywalled and was not checked. |
| `trade_lifecycle_operations` | VERIFIED | Tasks: practitioner judged all 3 record-checkable (capture trade; reconcile positions; settle trade). Cost: claimed range USD 150k-350k names JPMorgan Chase 2023 Form 10-K compensation disclosures and the Radford survey. JPMorgan Chase 2023 Form 10-K: compensation expense 46,465 (p.57) over 309,926 employees (p.46) is about USD 150k per employee; Corporate & Investment Bank 14,345 (p.72) over 74,404 (p.74) is about USD 193k. The CIB figure falls inside the claimed range; the firm-wide figure sits just below its lower bound. The Radford survey is paywalled and was not checked. |
| `global_banking_financing` | PARTIAL | Tasks: practitioner judged all 3 record-checkable (allocate loan syndication; commit a syndicated loan; process loan drawdown). Cost: claimed range USD 300k-600k names JPMorgan Chase 2024 CIB compensation over headcount. JPMorgan Chase 2024 Form 10-K: compensation expense 51,357 (p.62) over 317,233 employees (p.50) is about USD 162k per employee; Commercial & Investment Bank 18,191 (p.77) over 93,231 (p.80) is about USD 195k. The CIB figure sits below the claimed range. Reopen with a compensation source specific to financing bankers. |
| `listed_derivatives_client_clearing` | PARTIAL | Tasks: practitioner judged all 8 record-checkable. Cost: not shown to overlap. The claim of USD 180k-350k names Goldman Sachs 2024 compensation over headcount. Goldman Sachs full year 2024 earnings release (15 Jan 2025): compensation and benefits 16,706 over headcount 46,500 is about USD 359k per head. That sits just above the claimed range. The claim of USD 250k-500k names the Options Group report (paywalled, not checked) and JPMorgan 2023 personnel expense (about USD 150k firm-wide, USD 193k CIB), below the range. Reopen with a public dated compensation source for clearing roles. |
| `regulatory_reporting_conduct_compliance` | PARTIAL | Tasks: practitioner judged 2 of 3 record-checkable (MiFIR transaction report; retain books and records) and was UNSURE on "Prepare EMIR trade report"; three are required. Cost: claimed range USD 200k-450k names JPMorgan Chase 2023 Form 10-K compensation disclosures and the Radford survey. JPMorgan Chase 2023 Form 10-K: compensation expense 46,465 (p.57) over 309,926 employees (p.46) is about USD 150k per employee; Corporate & Investment Bank 14,345 (p.72) over 74,404 (p.74) is about USD 193k. Both figures sit below the claimed range; Radford is paywalled and was not checked. Reopen if the practitioner resolves the EMIR task and a compensation source overlaps. |
| `buyside_trading_execution` | UNVERIFIED | Tasks: practitioner judged 3 of 4 record-checkable and was UNSURE on "Produce transaction cost analysis"; the task half is met. Cost: not yet resolved. Claimed range USD 200k-400k names JPMorgan Chase 2024 compensation over headcount adjusted for buy-side roles. JPMorgan Chase 2024 Form 10-K: compensation expense 51,357 (p.62) over 317,233 employees (p.50) is about USD 162k per employee; Commercial & Investment Bank 18,191 (p.77) over 93,231 (p.80) is about USD 195k. Both sit below the range; the Asset & Wealth Management compensation expense is 7,984 (p.84) but its employee count (p.85 onward) was not reachable, so no conclusion is drawn. |

`clearing_settlement_custody` and `repo_secfin_collateral` now have two VERIFIED
anchor types among A1 to A3, a VERIFIED A4 row and no UNVERIFIED rows, so they are
fully corroborated under SPEC-01. `trade_lifecycle_operations` has a VERIFIED A4
row but its only A2 row is still UNVERIFIED.

Ledger totals after this review: 86 VERIFIED, 12 PARTIAL, 12 REFUTED, 181
UNVERIFIED of 291 rows. Two of 25 areas are fully corroborated; G6 still fails.

## Sources

- <https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/managements-discussion-analysis-2023.pdf>
- <https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/managements-discussion-analysis-2024.pdf>
- <https://www.goldmansachs.com/pressroom/press-releases/current/pdfs/2024-q4-results.pdf>
