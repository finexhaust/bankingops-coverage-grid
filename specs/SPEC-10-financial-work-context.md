# SPEC-10 — Financial-work context

Version 0.1.1. Status: **PROPOSED**. This extends BOCG's public reference model;
it does not constitute a new independently elicited or ratified coverage grid.

## Purpose

Readers need to understand how advisory, financing, investment activity,
transaction processing and control belong to a common financial-work surface.
An alphabetical division list hides that context and mixes business activities
with functions that support several businesses. This extension adds a parent
domain scheme and a separate capability vocabulary to the existing references.

The common root is **institutional finance and capital markets**. Proposed
domains are advisory/origination, investment management, markets/financing,
operations/servicing, and risk/control. A public area may have more than one
proposed parent. These are conceptual relationships, never an organisation chart
or an assertion that an institution performs the work.

Capabilities describe interpret, analyse, reconcile, decide, authorise, execute,
escalate, verify, and challenge/falsify. They are optional, unordered descriptors.
One valuable escalation or falsification may be sufficient for a useful task.
There is no requirement to demonstrate every capability and no admission filter.

## Public artifacts and derivation

- `reference/financial-work-context-proposals.v1.json` records the proposed
  definitions, placements, basis, method and public input paths.
- `reference/financial-work-context.v1.json` is the reproducible catalogue.
- `specs/financial-work-context.schema.json` describes the public output.
- `specs/financial-work-placement.schema.json` describes an optional,
  consumer-owned sidecar to an existing evidence surface.
- `tools/build_financial_work_context.py` builds, resolves or projects context.

The builder reads the public 42-area and 25-area matrix generations. Their union
contains 48 distinct division keys: 25 current and 23 historical-only. No
division is renamed, merged or declared retired. In particular, M&A remains
resolvable through its historical binding. Similar names and combined labels
never create an equivalence or automatic upgrade of an earlier reference.

The context proposal is model-assisted work requested by the owner. Public
BOCG definitions are its derivation inputs; no private corpus, seller coverage
or benchmark placements are inputs. The authoring agent had project context:
this is not a blind exercise or an independent multi-model result. Every new
domain, capability and parent placement is labelled PROPOSED. A later consensus
claim requires its own frozen, unseeded protocol. SPEC-01's existing prompts and
results are unchanged; these proposals are not inserted as elicitation examples.

Each source is hashed. The context digest covers the complete canonical JSON,
excluding only its own `context_sha256`. The release manifest includes the
catalogue, proposal inputs, schemas, builder and both source matrices. Definition
and membership changes require a new context revision and digest. Existing
operating-catalogue, task, control-point and evidence references retain their
original versions and meanings.

## Semantic contract

The extension uses the existing SPEC-04 standards layer: `skos:Concept`,
`skos:broader`, `skos:related`, and `prov:wasDerivedFrom`. See the
[SKOS reference](https://www.w3.org/TR/skos-reference/) and
[PROV-O](https://www.w3.org/TR/prov-o/).

Context membership is separate from a claim of exercised capability or coverage.
M&A and margin can share the institutional-finance root without being equivalent
activities, comparable evaluations or evidence for one another. A domain does
not inherit coverage from one child. A capability is never assigned to a task
solely because the task mentions a division.

Consumers may attach optional capability touchpoints with their own evidence
references, mapping status and review history. The sidecar pins the context
version and digest and carries opaque subject/evidence references only. Source
text, people, employer records, occurrence details and adjudication stay private.
This does not replace SPEC-08 or reinterpret its evidence-depth rule.

Projection preserves each consumer mapping status. Proposed placements do not
raise evidence depth, convert a candidate into an accepted task, or paint the
qualified public benchmark overlay. Unknown areas remain unresolved on the
output, not dropped. Invalid context pins or capability identifiers are metadata
errors; they are not reasons to reject otherwise useful trace candidates.

## Reading and using the catalogue

```sh
python3 tools/build_financial_work_context.py
python3 tools/build_financial_work_context.py --resolve ma_advisory
python3 tools/build_financial_work_context.py --project /path/to/consumer-placement.json
```

The first command produces public definitions without model calls or tests.
Resolution exposes the contextual parents and all source-snapshot bindings.
Projection consumes a private sidecar and writes its result to stdout; it never
adds that occurrence to the public catalogue. Empty capability lists are valid.

Consumer graphics can display benchmarks and corpus-derived candidates on this
common surface, distinguishing context status, candidate association and
qualified evidence. Any concentration of a consumer's cases is a result of that
consumer's feedstock and review subset. It is not a limit of the contextual
vocabulary or evidence of market-wide saturation, model headroom or uplift.
