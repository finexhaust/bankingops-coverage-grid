# A2 filing check - 27 November 2026

Scope: the 89 A2 (segment line-item) rows of `live-run-20261019/corroboration.csv`.
This check changes no elicitation prompt, raw response, alias, matrix, taxonomy key
or admission rule. It does not declare a release or satisfy G6 or G10.

## Method

All 89 rows cite six filings: JPMorgan Chase FY2023 and FY2024, Goldman Sachs
FY2023 and FY2024, Morgan Stanley FY2023 and Citigroup FY2023 Form 10-K, with 27
distinct line-item labels. An agent read each filing and searched for the label as
printed in a segment or revenue disclosure (SPEC-01 section 6: "line item string
appears in named filing for named FY"). Each ledger row names the checker, check
time, source, page and a verbatim quote. Rows that share a filing and label share
one decision.

The fetch tooling reached only part of each document. Where the segment tables
were not reached, the row stays UNVERIFIED with a note naming the unread pages.
No failed retrieval is treated as a refutation, and no row was marked REFUTED.
A label printed in a different form (for example "Banking & Payments" for
"Banking") is PARTIAL, which does not count toward G6.

## Results

| Status | Rows |
| --- | ---: |
| VERIFIED | 59 |
| PARTIAL | 5 |
| UNVERIFIED | 25 |
| Total | 89 |

Ledger totals after this check: 83 VERIFIED, 9 PARTIAL, 12 REFUTED, 187
UNVERIFIED of 291 rows. No division is fully corroborated.
`clearing_settlement_custody` and `repo_secfin_collateral` now hold two VERIFIED
anchor types and lack only their A4 row, which requires a named practitioner
reviewer.

| Bank | FY | Label as emitted | Status | Rows | Finding |
| --- | --- | --- | --- | ---: | --- |
| Citigroup Inc. | FY2023 | Markets | VERIFIED | 1 | Reportable segment and row in "Segment Revenues and Income (Loss)", Revenues table, 2023 Form 10-K: "Markets / 18,857 / 20,161 / 19,399". Citi was managed in five operating segments from 4Q23: Services, Markets, Banking, U.S. Personal Banking and Wealth. |
| Goldman Sachs Group, Inc. | FY2023 | Equities | VERIFIED | 4 | Item 1 (Business), Global Banking & Markets revenue sources, p.3 of the 2023 Form 10-K as published in the issuer annual report: "Equities. Equities generates revenues from intermediation and financing activities." The MD&A and Note 25 tables were not reached. |
| Goldman Sachs Group, Inc. | FY2023 | FICC | VERIFIED | 7 | Item 1 (Business), Global Banking & Markets revenue sources, p.3 of the 2023 Form 10-K: "FICC. FICC generates revenues from intermediation and financing activities." The MD&A and Note 25 tables were not reached. |
| Goldman Sachs Group, Inc. | FY2024 | Equities | VERIFIED | 4 | Item 1 (Business), Global Banking & Markets revenue sources, 2024 Form 10-K: "Equities. Equities generates revenues from intermediation and financing activities." The MD&A and Note 25 tables were not reached. |
| Goldman Sachs Group, Inc. | FY2024 | Fixed Income, Currency and Commodities (FICC) | VERIFIED | 7 | Item 1, Our Business Segments, 2024 Form 10-K: "Fixed Income, Currency and Commodities (FICC) intermediation and financing activities"; revenue caption "FICC. FICC generates revenues from intermediation and financing activities." |
| JPMorgan Chase & Co. | FY2023 | Asset Management | VERIFIED | 1 | Printed as a business of Asset & Wealth Management in the business segment structure chart, p.65 of the 2023 Form 10-K (MD&A extract published by the issuer; footer "JPMorgan Chase & Co./2023 Form 10-K"). |
| JPMorgan Chase & Co. | FY2023 | Equity Markets | VERIFIED | 3 | CIB "Revenue by business" table, p.72 of the 2023 Form 10-K: "Equity Markets 8,979 10,367 10,529" (USD millions, 2023/2022/2021). |
| JPMorgan Chase & Co. | FY2023 | Fixed Income Markets | VERIFIED | 7 | CIB "Revenue by business" table, p.72 of the 2023 Form 10-K: "Fixed Income Markets 18,813 18,617 16,865" (USD millions). |
| JPMorgan Chase & Co. | FY2023 | Investment Banking | VERIFIED | 3 | CIB "Revenue by business" table, p.72 of the 2023 Form 10-K: "Investment Banking $ 6,243 $ 6,510 $ 12,506" (USD millions). |
| JPMorgan Chase & Co. | FY2023 | Markets | VERIFIED | 9 | Executive overview table, p.49 of the 2023 Form 10-K: "Markets(c) 27,792 28,984 (4)"; footnote: "Markets consists of CIB's Fixed Income Markets and Equity Markets businesses." |
| JPMorgan Chase & Co. | FY2024 | Asset & Wealth Management | VERIFIED | 1 | Reportable segment column header in "Segment & Corporate Results - Managed Basis", p.72 of the 2024 Form 10-K; AWM total net revenue 21,578 (USD millions). |
| JPMorgan Chase & Co. | FY2024 | Asset Management | VERIFIED | 1 | AWM "Revenue by line of business", p.84 of the 2024 Form 10-K: "Asset Management $ 10,175 $ 9,129 $ 8,818" (USD millions). |
| JPMorgan Chase & Co. | FY2024 | Markets | VERIFIED | 8 | Executive overview table, p.54 of the 2024 Form 10-K: "Markets(c) 30,007 27,964 7"; Markets revenue table total net revenue 30,007, p.82. |
| JPMorgan Chase & Co. | FY2024 | Payments | VERIFIED | 1 | CIB "Revenue by business", p.77 of the 2024 Form 10-K: "Payments 18,085 17,818 13,490" (USD millions). |
| Morgan Stanley | FY2023 | Institutional Securities | VERIFIED | 1 | Reportable segment, Item 1 Business Segments, 2023 Form 10-K: "our business segments: Institutional Securities, Wealth Management and Investment Management." |
| Morgan Stanley | FY2023 | Investment Management | VERIFIED | 1 | Reportable segment, Item 1 Business Segments, 2023 Form 10-K (same sentence as Institutional Securities). |
| Goldman Sachs Group, Inc. | FY2023 | Investment Banking | PARTIAL | 2 | Printed as "Investment banking fees" under "Global Banking & Markets generates revenues from the following", Item 1, p.2 of the 2023 Form 10-K. No standalone "Investment Banking" segment or revenue label was seen; the MD&A and Note 25 tables were not reached. |
| JPMorgan Chase & Co. | FY2024 | Asset management | PARTIAL | 1 | The line item is printed "Asset Management" (capital M; AWM revenue by line of business, p.84 of the 2024 Form 10-K). The lower-case string appears only inside "Asset management fees". Recorded PARTIAL because SPEC-01 requires the label as printed; promote to VERIFIED only if a case-insensitive match is accepted. |
| JPMorgan Chase & Co. | FY2024 | Banking | PARTIAL | 1 | No standalone "Banking" label. Printed forms are "Banking & Payments" (CIB, p.77: "Total Banking & Payments 35,267") and "Banking & Wealth Management" (CCB, p.73) in the 2024 Form 10-K. |
| JPMorgan Chase & Co. | FY2024 | Corporate & Investment Bank | PARTIAL | 1 | In the 2024 Form 10-K this name appears only as a former segment ("former Corporate & Investment Bank and Commercial Banking business segments", p.70). The reportable segment is printed "Commercial & Investment Bank" (p.77). |
| Goldman Sachs Group, Inc. | FY2023 | Global Markets | UNVERIFIED | 2 | Not yet resolved. Item 1 of the 2023 Form 10-K uses only "Global Banking & Markets" (segments: Global Banking & Markets, Asset & Wealth Management, Platform Solutions). The MD&A and Note 25 tables were not reached; no refutation is inferred from unread pages. |
| JPMorgan Chase & Co. | FY2023 | Other | UNVERIFIED | 2 | Not yet resolved. No bare "Other" row in the segment or revenue tables read verbatim (pp.47-77 of the 2023 Form 10-K); nearest labels are "Credit Adjustments & Other(a)" (CIB revenue by business, p.72), "Other income(a)" (p.54) and "Other(b)" (noninterest expense, p.56). The Corporate segment pages (pp.81-85) were not read; no refutation is inferred from the unread pages. |
| JPMorgan Chase & Co. | FY2024 | Global Markets | UNVERIFIED | 7 | Not yet resolved. Not present in the 2024 Form 10-K MD&A text read verbatim (pp.52-84), where the label is "Markets". Pages 85 onward were not reachable; no refutation is inferred from unread pages. |
| Morgan Stanley | FY2023 | Equity | UNVERIFIED | 3 | Not yet resolved. The MD&A Business Segments tables (p.33 onward) and Note 22 were not reachable with the fetch tooling used; Item 1 does not print this label. |
| Morgan Stanley | FY2023 | Fixed Income | UNVERIFIED | 3 | Not yet resolved. The MD&A Business Segments tables (p.33 onward) and Note 22 were not reachable with the fetch tooling used; Item 1 does not print this label. |
| Morgan Stanley | FY2023 | Investment Banking | UNVERIFIED | 3 | Not yet resolved. The MD&A Business Segments tables (p.33 onward) and Note 22 were not reachable with the fetch tooling used; Item 1 does not print this label. |
| Morgan Stanley | FY2023 | Sales and Trading | UNVERIFIED | 5 | Not yet resolved. The MD&A Business Segments tables (p.33 onward) and Note 22 were not reachable with the fetch tooling used; Item 1 does not print this label. |

## Remaining A2 work

- Morgan Stanley FY2023: "Equity", "Fixed Income", "Investment Banking" and
  "Sales and Trading" need the MD&A Business Segments tables (p.33 onward) or
  Note 22.
- Goldman Sachs FY2023: "Global Markets" needs the MD&A segment tables or Note 25.
- JPMorgan Chase FY2024: "Global Markets" needs pages 85 onward of the 10-K MD&A.
- JPMorgan Chase FY2023: "Other" needs the Corporate segment pages (81 to 85).

A full-text copy of each filing (for example the EDGAR complete submission) would
settle all of these in one pass.

## Sources

- <https://www.goldmansachs.com/investor-relations/financials/current/annual-reports/2023-annual-report/multimedia/2023-annual-report.pdf>
- <https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/managements-discussion-analysis-2023.pdf>
- <https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/managements-discussion-analysis-2024.pdf>
- <https://www.sec.gov/Archives/edgar/data/831001/000083100124000033/c-20231231.htm>
- <https://www.sec.gov/Archives/edgar/data/886982/000088698225000005/gs-20241231.htm>
- <https://www.sec.gov/Archives/edgar/data/895421/000089542124000300/ms-20231231.htm>
