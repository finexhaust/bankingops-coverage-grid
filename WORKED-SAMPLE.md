# Worked sample: one finance-operations task with its verifier

This is one demonstration task, shown in full so the format can be judged. The institution, client, feeds, rulings, people and figures are invented. It is a sample, not part of any scored family, and its author-side and independent practitioner reviews are pending. The setting here is prime-brokerage financing; the first packaged family covers securities financing.

## What a task consists of

1. **A situation** a middle-office analyst would meet, written from the institution's own documents.
2. **The document set** the agent works from. Some documents conflict; at least one conflict can only be resolved by escalating.
3. **A rubric** whose lines each name one fact or decision, tagged retrieval, judgement or escalation.
4. **A declared answer**: a structured file with fixed fields, beside a prose memo and a client notice.
5. **Programmatic checks** on the declared fields, plus judge-graded lines for the prose. The checks carry known-good and known-bad answers, so the verifier's false-positive and false-negative rates are measured, not assumed.
6. **A monetary effect**: the amount the decisions turn on.
7. **A seal**: a digest over the task, rubric, checks and key, recorded before the task is scored. A sealed task is never revised; a correction is a new task with its own seal. This sample is itself such a correction of an earlier version.

## The task

**Id** FM-PB-0417-R2 · **Area** prime_brokerage_financing · **As of** Tuesday 26 May 2026, 08:40 New York · **Seal** `5ba26513da6ee786...`

### Situation (the prompt)

It is 08:40 New York on Tuesday 26 May 2026. Both US and GB calendars are open today; the GB bank holiday was Monday 25 May. On Friday 22 May, the last business day, Ficta Meridian's prime-brokerage desk issued a GBP 1,400,000 margin call to the client Harrow Ridge Capital against a portfolio collateralised in USD Treasuries. Overnight the stock-loan accrual engine ran on the US calendar only. The client's operations contact has emailed asking whether the call still stands and what will be instructed today. You are the middle-office analyst on the desk. Using the systems available to you, establish what accrued and what did not, decide whether the call stands at today's value date, decide what can be instructed before the DTC cutoff and which GBP value date and London settlement cutoffs apply, draft the client notice, and raise whatever break is required. Write your answer as a memo with an action list.

### Documents

**D1. Calendar service, extract for 25 to 26 May 2026**

```
25-May-2026  GB  BANK_HOLIDAY  (Spring bank holiday)   settlement: no GBP value date
25-May-2026  US  OPEN                                   DTC instruction cutoff 15:00 ET
26-May-2026  GB  OPEN                                   first GBP value date after holiday
26-May-2026  US  OPEN                                   DTC instruction cutoff 15:00 ET
```

**D2. Feed registry, accrual sources (as at 20 May 2026)**

```
feed_id  name                    calendar  accrual_role        status
FR-01    SL-ACCR-US              US        primary (USD legs)  active
FR-02    SL-ACCR-GB              GB        primary (GBP legs)  active
FR-03    SL-ACCR-LEGACY-PAIR-A   US/GB     retired 2026-04-30  inactive
FR-04    SL-ACCR-LEGACY-PAIR-B   US/GB     retired 2026-04-30  inactive
FR-05    COLL-VAL-USD            US        collateral valuation active
FR-06    FX-CLOSE-LDN            GB        FX fixing            active
FR-07    FX-CLOSE-NY             US        FX fixing            active
```

**D3. Treasury ruling TR-2026-041, dated 21 May 2026**

```
With effect from 22 May 2026, stock-loan accrual for cross-currency financing books is sourced from FR-01 for USD legs and FR-02 for GBP legs. Legs whose calendar is closed do not accrue on the closed day; the accrual is caught up on the next open day for that calendar. FR-03 and FR-04 must not be used. Any discrepancy between an engine run and this ruling is a break to be raised to Treasury Operations, not adjusted manually.
```

**D4. Runbook PB-RB-12, Holiday accrual handling, last revised 3 March 2026**

```
When one calendar is closed, run the accrual engine on the legacy pair (FR-03/FR-04) which handles both calendars, then reconcile in the morning.
```

**D5. Collateral schedule, Harrow Ridge Capital (extract)**

```
margin_call_threshold      GBP 250,000
call_validity              stands until value-dated settlement or recalculation
recalculation_trigger      any change to accrued financing or collateral value > 2%
fx_source_for_call         FR-06 (London close) when GB open; FR-07 otherwise
```

**D6. Ticket queue, 26 May 2026 08:15 ET**

```
TQ-88213  OPEN  Accrual engine completed 02:10 ET on US calendar only; GBP legs skipped; no break raised
TQ-88214  OPEN  Client email: Harrow Ridge asks if call GBP 1.4m stands and what settles today
```

### Rubric

| # | Criterion | Tag | Graded by |
|---|---|---|---|
| 1 | States that USD legs accrued overnight via FR-01 and GBP legs did not accrue on 25 May because the GB calendar was closed | retrieval | checks and judge |
| 2 | Cites TR-2026-041 as the authority for the accrual sources and the catch-up rule | retrieval | checks and judge |
| 3 | Identifies that runbook PB-RB-12 is superseded by TR-2026-041 (its legacy pair FR-03/FR-04 is retired and prohibited) and does not follow it | judgement | checks and judge |
| 4 | Concludes the GBP legs catch up on 26 May, the first GB open day, and that no manual accrual adjustment is permitted | judgement | checks and judge |
| 5 | Determines whether the call stands: it stands until recalculation, and recalculation is triggered only if accrued financing or collateral value moved more than 2 percent; the memo either shows the check or states the data needed and does not assert a new call amount without it | judgement | checks and judge |
| 6 | Names the 15:00 ET DTC cutoff for USD collateral; identifies 26 May as the first GBP value date and an open GBP day. Any GBP cash instruction is conditional on applicable London cutoffs and the recalculation check, not prohibited merely because 25 May was a holiday. | retrieval | checks and judge |
| 7 | Drafts a client notice that states the call's status, the reason (GB holiday accrual timing), the FX source rule (FR-06 today, London open) and the next value date, without inventing figures | judgement | checks and judge |
| 8 | Raises a break to Treasury Operations for TQ-88213 citing TR-2026-041, the feeds involved and the engine run time, rather than adjusting the accrual by hand | escalation | checks and judge |

### Declared answer

The agent writes one structured file with these fields.

| Field | Type | Meaning |
|---|---|---|
| `episode_id` | string | FM-PB-0417-R2 |
| `memo` | string | The memo to the desk, in prose |
| `action_list` | list | Ordered actions, one string each |
| `client_notice` | string | The draft notice to the client |
| `accrual_sources` | object | Feed id per currency leg, keys USD and GBP |
| `gbp_accrued_on_25_may` | boolean | Whether GBP legs accrued on 25 May |
| `authorities_cited` | list | Document IDs or references relied on as governing authority, excluding documents merely inspected and rejected as superseded |
| `runbook_pb_rb_12_followed` | boolean | Whether the runbook's legacy-pair procedure was followed |
| `manual_accrual_adjustment` | boolean | Whether any manual accrual adjustment is made or proposed |
| `gbp_catch_up_date` | string | Date the GBP accrual catches up |
| `call_status` | string | One of stands_pending_recalculation_check, void, recalculated |
| `new_call_amount_asserted` | boolean | Whether a new call amount is asserted without the 2 percent check |
| `dtc_cutoff` | string | The DTC instruction cutoff named |
| `instruct_today` | list | What is instructed today |
| `gbp_cash_instructed_today` | boolean | Whether any GBP cash leg is instructed for today's value |
| `gbp_cash_value_date` | string | Value date used for GBP cash legs |
| `fx_source_today` | string | FX fixing feed used for the call today |
| `break` | object | raised (boolean), to (team), ticket (the existing engine-run ticket being escalated), cites (document IDs or ruling references) |

### Verifier

15 positive checks and 3 penalty checks read the declared fields; penalties apply to forbidden actions, such as following the superseded runbook. The escalation line is scored on its own: an answer that resolves the conflict by hand fails it, whatever else it gets right. The checks' expected values, the answer key, the reference answer and the known-good and known-bad answers are sealed with the task and are not shown here.

### Monetary effect

GBP 1,400,000. Call issued 22 May; stands until value-dated settlement or recalculation; recalculation triggered only by a movement over 2 percent in accrued financing or collateral value. None executed yet. The call's status and the first GBP value date (26 May) determine what settles; a wrong answer either voids a standing call or instructs a GBP cash leg for a non-existent value date.

## What this sample does and does not show

- It shows the format: documents with a planted conflict, a rubric tied to documents, a declared answer and a programmatic verifier.
- It exports to Harbor and HUD task formats from one record.
- It is not a result. Pass rates, verifier error rates and practitioner signatures are reported for a packaged family, not for this sample.
- Passing the checks means agreement with the authored checks on a declared answer. It is not a statement of legal or regulatory compliance.
