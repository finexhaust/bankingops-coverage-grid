# SPEC-07 — Replayable compliance scenario contract

```
ARTIFACT : current definition-only contract for replayable compliance scenarios
STATUS   : v0.1 normative contract
SOURCE   : specs/replayable-compliance-scenario.schema.json
DEPTH    : composes public cell, task, input state, oracle and verdict shapes; never institution instances
```

## 0. Goal

A compliance scenario is a reproducible, content-addressed test of whether a
model release can correctly apply a BOCG control point to a bounded input
state. The contract stays above the SPEC-03 floor: it references public cells
and tasks, defines the shape of a scenario, an oracle, and an expected verdict,
but never includes an institution's private evidence, workflow or corpus.

## 1. Non-negotiable invariants

```
S7-I1 RELEASE_PINNED      every scenario names a BOCG release manifest by hash and a model release by identifier and version.
S7-I2 CELL_PINNED         every scenario references exactly one curated or proposed control-point cell by cell_id.
S7-I3 TASK_PINNED         every scenario references exactly one operating-catalogue task (division_key + task label digest).
S7-I4 ORACLE_PUBLIC       the oracle is a public, deterministic function definition (rule set, reference table or standard clause); no private corpus material.
S7-I5 EXPECTED_VERDICT    the scenario declares one expected verdict from a closed vocabulary.
S7-I6 INPUT_STATE_BOUNDED the input state contains only synthetic or publicly referenceable facts needed to exercise the cell.
S7-I7 REPLAY_HASHED       the scenario carries a deterministic scenario hash over cell, task, input state, oracle and expected verdict.
S7-I8 NO_OCCURRENCE_CLAIM a scenario is a test fixture, not an assertion that any institution experienced the facts.
```

`manifest_sha256` is the canonical self-digest: SHA-256 of canonical JSON for
the manifest with `manifest_sha256` omitted. It is not the digest of the
manifest file's raw bytes. `cell_ref.cell_sha256` is SHA-256 of the exact raw
bytes of the pinned cell JSON artifact. `scenario_hash` is SHA-256 of canonical
JSON containing exactly `cell_ref`, `task_ref`, `input_state`, `oracle`, and
`expected_verdict`; `scenario_hash` and all other scenario fields are excluded.
Canonical JSON is UTF-8 JSON with non-ASCII characters preserved, sorted keys,
and compact separators.

## 2. Verdict vocabulary

A verdict expresses the result of applying the cell's control point to the
input state through the oracle.

- `compliant` — the input state satisfies the control point.
- `non_compliant` — the input state violates the control point.
- `indeterminate` — the oracle cannot decide from the bounded input state.
- `out_of_scope` — the input state is outside the cell's stated division or task.

## 3. Run ledger

When a scenario is executed, the runner records:

- the BOCG release manifest hash;
- the model release identifier and version;
- the scenario hash;
- the actual verdict;
- a replay hash of the runner version and runtime parameters.

The current ledger schema is `specs/scenario-run-ledger-rows.schema.json`.
The older run-level schema is superseded and retained as a separate compatibility
contract.

## 4. Boundary

SPEC-07 does not publish model weights, inference logs, institution data or
adjudication decisions. Consumers may use the contract to build private
scenario suites and share only scenario hashes, run hashes and verdict counts.
