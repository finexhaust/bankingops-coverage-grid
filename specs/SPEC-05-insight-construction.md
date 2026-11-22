# SPEC-05 — Portable insight-construction and adjudication contracts

```
ARTIFACT : static definitions and rubrics for evidence-grounded insights
STATUS   : v0.3 normative profile
SOURCE   : specs/insight-construction-profile.yaml
BOUNDARY : definitions and conformance only; no institutional instances
```

## Purpose

This profile is a second, layered BOCG contract. SPEC-04 remains the public
division/function/control-point profile and continues to prohibit occurrence
instances. SPEC-05 defines portable shapes that an implementation may use for
Observation Atoms, Traces, Episodes, institutional speech-act expansion and
adjudication. It does not publish any firm's emails, workflow, people, systems,
graph, extraction logic or adjudication ledger.

## Normative separation

```text
BOCG:       schemas + vocabulary + rubrics + conformance fixtures
consumer:   extraction + instance data + inference + persistence + UI
```

An Observation Atom is an independently addressable, evidence-bound
proposition. A Trace orders or relates Atom identifiers without asserting
causality merely from order. An Episode is defeasible connective tissue among
Atoms; its existence does not make every inferred actor, cause or outcome true.

## Institutional speech acts

Implementations MUST preserve the literal speech act separately from a
defeasible institutional reading. One source span MAY support multiple Atoms.
The lifecycle states `directed`, `scheduled`, `executed`, `completed` and
`verified` are non-interchangeable. A directive MUST NOT establish execution,
completion or verification.

Composed-object lifecycle is separate from occurrence lifecycle. Composition
states include `draft`, `candidate`, `reviewed`, `admitted`, `qualified`,
`recomposition_required`, `rejected` and `withdrawn`; review state may be
`unreviewed`, `current` or `stale`, with an append-only review history.
`TraceHypothesisGroup` groups Trace hypotheses while explicitly asserting no
single process instance. A rejection carries a reason, attribution and whether
it may be reopened. Episodes may carry unresolved questions typed against the
registered question vocabulary.

## Temporal anchors and deadlines

Episode and obligation-frame records may carry typed temporal anchors
(`observed_at`, `valid_from`, `valid_to`, `deadline`, `scheduled_at`,
`executed_at`, `completed_at`, `verified_at`). An observation timestamp never
supplies a validity bound, and a scheduled time never proves execution. Deadline
constraints name a deadline type (`regulatory`, `contractual`, `internal_sla`,
`market_cutoff`) and a reference time; they express when a state is due, not that
it occurred. Unknown timestamps remain unknown.

An anchor may use the legacy `timestamp` date-time, or `time` with an explicit
`precision` and `value`: `instant` is a date-time, `date` and `business_date`
are YYYY-MM-DD, `month` is YYYY-MM, and `year` is YYYY. An `interval` has
`start` and `end` points, each with its own precision. Bounds are inclusive;
consumers MUST reject reversed intervals and MUST NOT infer a clock time or
greater precision. The same structured values are available for transition
`occurred_at` and deadline `reference_time`; their legacy date-time strings
remain valid.

For ordering without a date, an anchor may instead carry `relation` with
`order` (`before`, `after`, or `same_window`) and the `anchor_id` of another
anchor in the same Episode. Referenced anchors MUST exist, identifiers MUST be
unique, and an anchor MUST NOT refer to itself. These cross-record and interval
ordering constraints require consumer validation beyond JSON Schema. Relations
do not imply causality or a timestamp. Consumers may omit unknown anchors.

Lifecycle states are also deadline-bearing transitions. Each state MAY remain a
plain vocabulary value or MAY be a `LifecycleStateTransition` carrying an
optional `occurred_at` timestamp that MUST be grounded in a source span, per the
episode-feasibility rubric's `source_grounded_temporal_anchor` signal. A state
MAY also carry a `deadline_ref` expressing the regime clock expression (for
example `T+1 business day`, `EMIR reporting deadline`, `CSA notification time`)
together with the citation it derives from, and a `calendar_ref` identifying the
business-day calendar used to interpret that expression. These temporal fields
are optional and occur on transitions, not on abstract vocabulary values.

Dated settlement and cutoff events in a published sample MUST name a
`calendar_ref`. S5-G6 resolves it against
`reference/business-calendars.v1.json`, whose listed sources and coverage years
bound what can be checked. An event marked open MUST NOT fall on a weekend or a
listed holiday. Dates outside a calendar's stated coverage are rejected rather
than treated as business days. The generic `firm-internal calendar` example has
no published coverage; an institution-specific schedule is required before it
can validate dated events.

## Adjudication

Machine constructions are immutable. Adjudications record a labelled basis
(including owner/SME attestations and attestations held as assumptions), and
content origin distinguishes source-observed, author-supplied, machine-inferred
and attested content. An independent-provenance weight is recorded when claimed.
SME decisions are append-only overlays, bound to exact evidence and the prior
machine construction. Split decisions retain the original Atom and produce
content-addressed component Atoms sharing the same evidence selector.
Dependent Traces and Episodes require explicit recomposition.

The feasibility rubric's prerequisites are diagnostics only. Its versioned
`FEASIBLE` and `STRONG` classes describe evidence-density bands, not truth or a
retention gate. A score below a class threshold does not delete an Episode, and
an assessment may have no outcome. The five-family rubric prefers
`INDETERMINATE`; `UNCERTAIN` remains a compatibility synonym.

## Portability boundary

Normative artifacts contain no institution names, employee identities, corpus
paths, source text, workflow instances, customer data or implementation code.
Consumers pin a BOCG release manifest and fail closed on hash mismatch.
