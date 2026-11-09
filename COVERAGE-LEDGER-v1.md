# BOCG Coverage Ledger v1

**Public evaluation coverage of model-elicited capital-markets operational divisions.**

Sweep date: 2026-11-07 (UTC). Protocol version: `coverage-sweep/v1`.
Division set: BOCG live run `20260826`, prompt `efd90b74`, 42 divisions.

---

## 1. What this document is

BOCG (BankingOps Coverage Grid) elicited a taxonomy of a G-SIB's capital-markets operational
divisions from frozen base models under a byte-fixed prompt that forbids the vocabulary of the
target domain. The division set is therefore **not authored by us**: it is what the models
themselves name when asked to enumerate the divisions of a G-SIB, with anchors required *before*
the division name (invariant I5) so that backwards rationalisation is detectable.

This ledger performs one operation: it subtracts **public evaluation coverage** from that
model-elicited division set, and reports what is left.

Both sides of the subtraction are external to us. We did not choose the divisions (the models did)
and we did not choose the evals (the public registries did). The residue is the finding.

---

## 2. Classification scheme

Every eval encountered is classified into exactly one of:

| Class | Meaning |
|---|---|
| `DOC_QA` | question answering over text or filings |
| `NUM_REASON` | numerical/mathematical reasoning over financial data |
| `SENTIMENT_CLASS` | sentiment, classification, NER, intent, tagging |
| `KNOWLEDGE_RECALL` | exam-style or factual recall (CFA, CPA, MMLU-family) |
| `OPERATIONAL_PROCESS` | **requires performing or deciding a step in an actual institutional workflow**: booking, reconciling, margining, collateral, settlement, lifecycle events, limit/exception handling, onboarding, trade capture, financing decisions |
| `OTHER` | anything else (deliverable production, trading P&L, safety, text-to-SQL) |

The boundary between the first four and `OPERATIONAL_PROCESS` is the entire point. An eval that asks
questions *about* an operational topic is `DOC_QA` or `KNOWLEDGE_RECALL`, **not**
`OPERATIONAL_PROCESS`. This rule was applied conservatively throughout: where an item was arguable,
it was classified *out* of `OPERATIONAL_PROCESS`.

Per-division coverage disposition:

| Disposition | Meaning |
|---|---|
| `NONE` | no eval of any class found addressing this division by protocol v1 |
| `ADJACENT_ANALYTICAL` | evals exist on the division's subject matter, but test analysis/QA/deliverables, not the operational process |
| `ADJACENT_RETAIL` | operational evals exist, but on the consumer/retail side of the same product |
| `PARTIAL` | an operational eval exists that touches part of this division |
| `DIRECT` | an operational eval addresses this division |

`NONE` in this ledger means **`none_found_by_protocol_v1`**: absence of evidence under a stated,
reproducible procedure, on a stated date. It is not a claim that nothing exists anywhere.

---

## 3. Registries swept, with denominators

| Registry | Version / commit | Total tasks or envs | Finance-relevant | `OPERATIONAL_PROCESS` finance |
|---|---|---|---|---|
| EleutherAI lm-evaluation-harness | `d6de8164` (2026-09-14) | **13,125** runnable tasks | 433 (3.3%) | **0** |
| Stanford HELM | `63754d05` (2026-06-05) | **311** run specs / 290 scenarios | 11 (3.5%) | **0** |
| UK AISI Inspect Evals | docs registry, v0.27.0 sdist (2026-10-30) | **185** listings | 5 | 3, all retail or corporate back-office |
| PrimeIntellect-ai/prime-environments | `cf220ee8` (2026-05-07) | **109** environments | 4 | 1 (AgentDojo banking, retail) |
| PrimeIntellect `verifiers` examples | `72d08a0b` (2026-11-06) | **19** environments | 0 | 0 |
| METR/task-standard | `83ad6fd1` (2026-10-07) | **15** families | 0 | 0 |
| METR/public-tasks (deprecated) | `e2027dff` (2026-10-20) | **28** families / 186 tasks | 0 | 0 |
| Academic / published benchmarks | arXiv + PwC sweep | **52** retrieved | 52 | 5, all 2026, none capital-markets ops |
| Commercial eval vendors | 11 vendors, public pages | n/a | n/a | 1 near-miss (Snorkel), wrong domain |

**Open-registry total: 13,436 evaluation tasks in the two largest registries, of which the number
classified `OPERATIONAL_PROCESS` in finance is zero.**

---

## 4. The ledger: 42 divisions

`support` = number of eligible model families (of 5) naming the division; `k` = samples at 3/3.
Eligible families in run `20260826`: claude-opus-5, deepseek-v4-pro, gpt-5.6-sol, kimi-k3,
qwen3.6-35b. Three models excluded with declared reasons (see §6).

### 4.1 Unanimous consensus

| division_key | support | coverage | nearest public artifact |
|---|---|---|---|
| `prime_brokerage_financing` | **5/5 at 3/3** | **NONE** | nothing of any class |

This is the **only division in the 42 with unanimous support from every eligible family at full
sample agreement**, and it has no public evaluation coverage of any class.

### 4.2 Strong consensus (support 4–5)

| division_key | support | coverage | nearest public artifact |
|---|---|---|---|
| `equities_trading` | 5 | `ADJACENT_ANALYTICAL` | StockBench, FinTradeBench, InvestorBench: buy-side P&L, not sell-side market-making |
| `rates_trading` | 4 | `ADJACENT_ANALYTICAL` | as above; no rates desk process |
| `credit_trading` | 4 | `ADJACENT_ANALYTICAL` | as above |
| `commodities_trading` | 4 | `ADJACENT_ANALYTICAL` | as above |
| `securitised_products` | 4 | **NONE** | none |

### 4.3 Capital-markets operations: the cluster with nothing

| division_key | support | coverage | nearest public artifact |
|---|---|---|---|
| `collateral_margin_management` | 1 | **NONE** | ISDA CSA clause-extraction study: document extraction, not margining |
| `repo_secfin_collateral` | 2 | **NONE** | none |
| `trade_lifecycle_operations` | 3 | **NONE** | none |
| `listed_derivatives_client_clearing` | 2 | **NONE** | none |
| `custody_asset_servicing` | 1 | **NONE** | none |
| `product_control_ipv` | 1 | **NONE** | none |
| `xva_counterparty_risk` | 2 | **NONE** | none |
| `regulatory_transaction_reporting` | 1 | **NONE** | none |
| `market_risk_valuation_control` | 1 | **NONE** | none |
| `market_risk_management` | 1 | **NONE** | none |
| `treasury_balance_sheet_funding` | 0 | **NONE** | none |
| `model_risk_management` | 0 | **NONE** | none |
| `trade_surveillance` | 1 | **NONE** | ReguSim/ReguBench (2026): surveillance monitor, no repo, no task count |
| `client_lifecycle_kyc` | 0 | **NONE** | AMLBench (2026): graph retrieval over Ethereum transfers, no authorisation decision |
| `electronic_execution` | 0 | **NONE** | none |

### 4.4 Origination and advisory

| division_key | support | coverage | nearest public artifact |
|---|---|---|---|
| `dcm_origination` | 2 | `ADJACENT_ANALYTICAL` | BankerToolBench, Mercor APEX IB, Vals EMB, SnorkelFinance 2.0: deliverable production |
| `ecm_origination` | 1 | `ADJACENT_ANALYTICAL` | as above |
| `ma_advisory` | 0 | `ADJACENT_ANALYTICAL` | as above |
| `capital_markets_origination_combined` | 1 | `ADJACENT_ANALYTICAL` | as above |
| `leveraged_finance_loan_capital_markets` | 0 | **NONE** | none |
| `municipal_public_finance` | 0 | **NONE** | none |
| `institutional_sales_coverage` | 1 | **NONE** | none |
| `sellside_research` | 1 | `ADJACENT_ANALYTICAL` | FrontierFinance, SECQUE, Finance Agent Benchmark: research output, not production process |

### 4.5 Remaining divisions

| division_key | support | coverage |
|---|---|---|
| `fx_trading` | 3 | `ADJACENT_ANALYTICAL` |
| `em_trading` | 2 | `ADJACENT_ANALYTICAL` |
| `equity_derivatives_structured` | 2 | **NONE** |
| `cross_asset_structuring` | 1 | **NONE** |
| `macro_combined_rates_fx_em` | 1 | `ADJACENT_ANALYTICAL` |
| `ficc_combined` | 1 | `ADJACENT_ANALYTICAL` |
| `commodities_physical_operations` | 0 | **NONE** |
| `buyside_trading_execution` | 3 | `ADJACENT_ANALYTICAL` |
| `buyside_portfolio_management` | 2 | `ADJACENT_ANALYTICAL` |
| `buyside_investment_operations` | 0 | **NONE** |
| `buyside_investment_compliance` | 0 | **NONE** |
| `buyside_performance_risk_reporting` | 0 | **NONE** |
| `buyside_ldi_overlay` | 0 | **NONE** |

---

## 5. Findings

**F1. Zero direct coverage found.** Of 42 model-elicited capital-markets operational divisions, the
number with an `OPERATIONAL_PROCESS` evaluation found by this protocol across the enumerable registries
is **zero**. This does not extend to the sources section 7 records as unknown: the full Prime Intellect
Environments Hub, METR's non-public suite and login-gated commercial catalogues.

**F2. The gap is widest exactly where consensus is strongest.** `prime_brokerage_financing` is the
only division carrying unanimous 5/5 family support at 3/3 samples, and its coverage is `NONE`:
not adjacent, not partial, nothing of any class.

**F3. What operational finance evals do exist are on the wrong side of the counter.** The only
programmatically-verified operational finance environments in any public registry are
`tau2_banking` (97 tasks, retail servicing), AgentDojo's banking suite (16 user + 9 injection,
retail payments), TheAgentCompany's 9 finance tasks (corporate AP/payroll/expenses), Bank-World
(50 tasks, retail/lending, **closed source**), CXBench banking (20 of 120 tasks, consumer
disputes), and Galileo's banking domain (100 scenarios, retail contact-centre). Every one is
consumer or corporate back-office. None is institutional.

**F4. The registries' format cannot express the work.** lm-eval-harness and HELM are built around
static question–answer pairs scored by exact match, F1 or an annotator. That format cannot
represent a multi-step operational process with state, which is a structural reason for F1 rather
than an oversight.

**F5. One commercial vendor has the right mechanism and the wrong domain.** SnorkelFinance 2.0 runs
agents in Docker/OpenEnv with stateful sessions and MCP tools, and **programmatically verifies
expected state changes in 69.5% of its 200 tasks**, the correct architecture. Its declared scope
is investment banking and private equity advisory. Collateral, margin, settlement, stock loan,
swaps lifecycle, reconciliation and booking are not mentioned.

**F6. No vendor claims this territory.** Across Vals AI, Patronus, LayerLens, Artificial Analysis,
Scale/SEAL, Bespoke Labs, Galileo, Braintrust, Arize, Haize Labs, Snorkel and Mercor, **not one
publicly claims coverage of prime brokerage, securities financing, equity finance, stock loan,
swaps lifecycle, collateral management, margin, or post-trade.** Those terms appear on none of
their benchmark pages, leaderboards or papers.

---

## 6. Independent corroboration

The finding is not ours alone, and it reproduces under a **different taxonomy**.

[*Meta-Benchmarks for Financial-Services LLM Evaluation*, arXiv 2607.01740](https://arxiv.org/pdf/2607.01740)
catalogues **452 benchmark identifiers** and maps them onto the **BIAN Service Landscape 14.0.0**,
an industry-standard banking taxonomy with no relation to BOCG. It reports that **only 24 of 41
generalised work activities are exercised by any public benchmark**, i.e. 17 have no coverage at
all, and concludes that *the public benchmark ecosystem concentrates on information-processing
work*. BIAN's Collateral Administration, Market Operations, Trade Banking and Wholesale Trading
domains receive scores only as **proxies** mapped from general activities such as "Analyzing Data
or Information"; no benchmark exercises them.

A second survey, [arXiv 2602.19073](https://arxiv.org/html/2602.19073v1), names no benchmark
covering reconciliation, settlement, collateral, trade booking, corporate actions or securities
lending; its "decision-making" category is M&A and trading, and its "risk management" category is
credit scoring and fraud detection.

**Two independent maps, one elicited cold from frontier models and one an industry standard, locate
the same uncovered territory.** That convergence is stronger evidence than either alone.

---

## 7. Declared limits of this sweep

Stated so the ledger can be checked and attacked:

1. **The Prime Intellect Environments Hub could not be enumerated.** It is a client-rendered
   application; its public API exposes no hub-listing endpoint, and the CLI contains none. The only
   window was `sitemap.xml` (102 URLs, 100 environment pages, fetched 2026-11-07), which is a
   featured subset, not the catalogue. Of those 100, zero were finance. **The Hub's true denominator
   is unknown, and it is the registry most likely to be growing fastest.** This is the largest open
   gap in this ledger.
2. **METR's non-public suite** (HCAST, RE-Bench, the time-horizons set) is not publicly enumerable.
3. **Login-gated commercial catalogues were not accessed.** LayerLens's claimed 50+ benchmarks could
   not be enumerated (two docs paths returned 404). Artificial Analysis's `AutomationBench-AA`
   finance slice is a private dataset and its detail page errored; structurally it could be
   operational, and it is recorded as **unknown, not as absence**.
4. **Sizes and grader types are unretrieved for 8 academic entries**; those cells were left blank
   rather than filled from memory.
5. **Bank-World** (arXiv 2610.39733) is the closest published fit to the operational definition. It
   is single-author, and its environments, graders and trajectories are private, access by email
   request. It is therefore not reproducible and not a public eval, but it is evidence that others
   have begun moving into this territory, **in the last month**.
6. **`gh api` was blocked by egress policy** for two repositories; both were enumerated instead from
   full `git clone` working trees and the PyPI sdist, so the counts are from real trees, not memory.
7. **No sweep script or per-item classification data is committed with this ledger.** Section 3 states
   the registries and section 2 the classification rule, so the sweep can be repeated by hand, but
   individual classification decisions cannot be audited from this repository.

## 8. Panel provenance

Run `20260826`, prompt `efd90b74`. Five eligible families at k≥3. Three models excluded, each with
a written reason retained in `exclusions.json` and their raw responses published with the bundle:

- `gemma-4-31b` (google): 0/3 valid. All three samples emitted `name` before `a1_regulatory`
  (offset 68 vs 149 in sample 0): the division named first, anchors supplied afterwards. Excluded
  **on merit**, as the backwards-rationalisation that invariant I5 exists to detect.
- `x-preview-f-free` (opencode-zen): 1/3 valid. Same failure mode in 2 of 3; one sample truncated.
  Below the k≥3 threshold; its single valid sample is retained in the matrix as a 0.33 cell for
  transparency.
- `glm-5.2` (zhipu): 0/3 valid. Transport and length failures, not a content judgement. **If a
  later retry yields three valid samples this exclusion must be removed and the matrix rebuilt.**

That the order-of-fields rule separates the panel (three families comply, two rationalise backwards)
is itself a reportable result about elicitation method, independent of the coverage finding.

---

*Protocol `coverage-sweep/v1`. Reproduce by re-running the §3 registries at the stated commits with
the §2 classification rule. Corrections to any row are welcome and will be versioned.*
