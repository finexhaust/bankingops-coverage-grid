# Release changes

## Unreleased

- SPEC-10 financial-work context 0.1.1 (PROPOSED): the display label of area
  `repo_secfin_collateral` reads "repo, securities finance and collateral"
  instead of the abbreviated "repo secfin collateral". The division key,
  reference ID, placement, domain links, snapshot bindings and every other
  area are unchanged; only the label, version and digests move.
- Corroboration ledger `live-run-20261019/corroboration.csv`: `claude-fable-5-1`
  (agent) checked the 31 A1 regulatory anchors of the six ISDA-adjacent areas against source (eCFR point-in-time
  2026-10-29, EU Publications Office Cellar OJ texts, FINRA, BIS, Cornell LII for 7 U.S.C.
  § 2). 24 VERIFIED, 4 PARTIAL, 3 REFUTED (17 CFR 23.494 does not exist; 17 CFR 1.33 does
  not govern swap dealer registration; MiFIR Art. 27 is reference data, not best
  execution). A subsequent OpenAI GPT-6 Astra Pro agent check against primary
  sources refuted nine additional occurrences of these incorrect citations and
  corrected two PARTIAL EMIR Article 39 notes without upgrading their status.
  Ledger totals: 24 VERIFIED, 4 PARTIAL, 12 REFUTED, 251 UNVERIFIED. Summary and
  grid rebuilt; no division is fully corroborated and G6 still fails (#45).
  The generation gate suite was executed on 2026-11-04; the report records
  G1–G5/G7–G9 PASS and G6/G10 FAIL after the companion G9 repair carries the
  recorded eligibility policy into replay and checks both matrix artifacts.
  These changes do not declare a tagged release.
- Repair provenance validation: resolve historical overlays and scenario pins
  through verified offline snapshots of the published v0.6.2 and v0.6.3
  manifests. Check historical denominators and every identifier against the
  pinned release; reject control-point paint, malformed manifests, unknown
  pins and altered artifacts. Preserve the existing 42/1/41 overlay unchanged.
- Validate each cell history key against its named taxonomy matrix. Record the
  original `post_trade_settlement` binding explicitly as UNADMITTED; it was an
  erroneous historical binding, not a division retired by regeneration.
- Fix G9 replay to carry the frozen exclusions policy and verify both matrix
  CSV and JSON. The October matrix reproduces exactly; generation evidence,
  model eligibility and admission outcomes are unchanged.
- Add PROPOSED cell `cp_isda_curve_input_completeness` under `market_risk_management`:
  the ISDA standard curve set required by a scheduled risk batch is complete and
  sourced before the batch runs (ISDA CDS Standard Model; Basel Framework MAR31;
  BCBS d457). Gives the FinExhaust ISDA curve replay a published cell to pin
  (#44).
- Re-bind control-point cells to the 2026-10-19 taxonomy (`live-run-20261019`):
  - Eleven cells named division keys absent from the regenerated matrix
    (`collateral_margin_management`, `regulatory_transaction_reporting`,
    `client_lifecycle_kyc`); a twelfth carried the previously unadmitted
    `post_trade_settlement` binding. Each is re-bound to the nearest
    admitted key and keeps its prior binding in a new optional
    `division_key_history` field (key, run, date, reason).
  - Add SPEC-03 invariant S3-I7 ADMITTED_KEY_BOUND and gate S3-G5: a non-RETIRED
    cell must name a key in the matrix of the run selected by
    `reference/taxonomy-source.json`. Previously a stale key passed every gate
    because only CURATED cells are checked by the catalogue builder.
  - Update the derivatives documentation vocabulary gap and `docs/isda-overlap.md`
    for the regenerated taxonomy. No cell content, citation or status changed.
- Add SPEC-10 financial-work context 0.1.0 (PROPOSED): five parent domains,
  nine optional capability descriptors, 48 retained area keys across the two
  public taxonomy generations, source hashes and an optional consumer sidecar.
  Context is distinct from coverage; no task admission rule or new evidence
  promotion is introduced. Existing division/function/task/control-point IDs,
  public benchmark rulings and source catalogues remain unchanged.
- Extend common semantics to profile 0.5.0 and include the context artifacts,
  builder and source matrices in release manifests. No tests, gate suites,
  fresh model calls or independent adjudication were run for this extension.

## v0.6.3 — 2026-10-17

- Meridian-facing public-eval observatory + cleanroom companion pin:
  - `reference/cleanroom-eval-companion.v1.json` pins cleanroom-eval **1.2.0**
    (`github_release_published` on `d01e56e35dd1…`).
  - `reference/public-eval-observatory.v1.json` projects LLMAJ live outcomes
    (Mercor / Rogo / BankerToolBench empty-intersection → `paint_eligible: false`)
    plus overlay paint rows for Lab consumers.
  - S9-G6 gate; `integrations/ficta-meridian/` Finexhaust apply pack
    (`apply-to-finexhaust.sh`, patched generator, Lab UI, footer version pin).
  - Catalogue / matrix / cells / task-concepts remain byte-compatible with v0.6.2.

## v0.6.2 — 2026-09-25

- SPEC-09 public-eval LLMAJ purity: front-loaded prereg + observable frozen prompt:
  - Lock prompt, rubric, inventory/catalogue digests, band weights, call settings
    and non-influence rules in `reference/public-eval-llmaj-prereg.v1.json`
    (`prereg_sha256` `dfcc901848f8…`).
  - Forbid owner-authored PENDING/PROPOSED `public_benchmark` rows and per-artifact
    prompt variants (would steer relative saturation or seller own coverage).
  - Live primary+sensitivity run under the locked prereg
    (`live-run-public-eval-llmaj/dfcc901848f8/`): four public_benchmark cards
    (Mercor Apex1 IB, Mercor Apex Agents, Rogo Big Finance Bench, Handshake
    BankerToolBench). Exact mapping-key intersection was empty on every card;
    ledger records four `paint_eligible: false` cases; no `public_benchmark`
    QUALIFIED paint promoted. Harvey LAB peer-shape L1 seed remains the only paint.

## v0.6.1 — 2026-09-25

- SPEC-09 public-eval surface overlay (correct paint scope):
  - Inventory is public peers / public rubrics-benchmarks-evals only; BOCG
    control-point citations and own rubrics do not paint saturation.
  - Likelihood-matched map (`L1`–`L3`) onto the SPEC-08 depth ladder; derived
    `division_rollup` for saturation vs voids (no presentation-standard artifact).
  - S9 gates; CONFORMANCE.md row 19; release-manifest binding.
- Catalogue, matrix, cells and task concepts remain byte-compatible with v0.6.0
  for evidence bindings; overlay is a supplement.

## v0.6.0 — 2026-09-24

- Add SPEC-08 task concepts and episode surface:
  - Group the released function and task definitions into concepts, one
    division at a time, with per-division provenance. `AUTO` divisions are
    machine-clustered by a deterministic, parameter-hashed method and are
    labelled as unread; `REVIEWED` divisions carry argued merges from
    `reference/task-concept-rulings.yaml` with a named reviewer, a date and a
    rationale per alias.
  - Rule `prime_brokerage_financing` REVIEWED: the released margin tasks split
    into compute-requirement and issue-and-collect concepts by terminal state,
    and nine composite role labels merge into one function concept (23
    aliases). The other 41 divisions stay AUTO.
  - Publish `reference/task-concepts.v1.json`, its schema, the rulings, the
    episode-surface schema, a synthetic surface fixture and the depth rule
    (`tools/episode_surface.py`): evidence depth is the deepest ratified
    touchpoint; candidates never raise it.
  - Add S8 gates and CI reproduction of the concept file; bind the new
    artifacts into the release manifest.
- The operating catalogue, coverage matrix, control-point cells and semantic
  profile are byte-identical to v0.5.0. Consumers pinned to an earlier release
  keep their evidence bindings.
- All changes remain above the SPEC-03 floor: definitions, schemas and rubrics
  only. No institution instance, corpus material or workflow claim is included.

## v0.5.0 — 2026-09-20

- Close ISDA regulatory overlap gaps (EPIC #6):
  - Add ISDA public standards (CDM, FpML, DSB UPI, ISO 20022) to SPEC-04.
  - Document in SPEC-04 that CDM/FpML model trade, event and legal agreement
    while the grid models division, function and control point, and that
    mappings are never identity assertions.
  - Extend mapping-policy usage notes so all declared standards, including the
    ISDA-adjacent entries, use only `close-match`, `related-match`,
    `narrower-than` or `schema-correspondence`.
  - Promote `derivatives_documentation_control` to `candidate_vocabulary_gaps`
    and record the non-normative derivatives trading documentation control
    candidate draft.
  - Author PROPOSED control-point cells for ISDA-native margin, reporting,
    confirmation, Determinations Committee and documentation controls, including
    a dedicated DC outcome-application cell under credit trading, four
    additional UMR/SIMM/CSA margin cells, and
    six reporting/confirmation cells (CFTC Part 43, EMIR REFIT UTI pairing,
    MiFIR Art. 26, OTC confirmation timeliness, portfolio reconciliation and
    reporting-error remediation).
  - Add SPEC-07 replayable compliance scenario contract and scenario run ledger
    schema (model release, manifest hash, scenario hash, verdict), plus the
    operational scenario schema, synthetic fixture, append-only row ledger and
    S7 conformance gates.
  - Add time and deadline semantics for SPEC-05 lifecycle states, including
    optional per-state `occurred_at` / `deadline_ref` / `calendar_ref`
    transitions alongside episode-level temporal anchors.
  - Publish G6 corroboration priority draft for ISDA-adjacent division keys and
    `docs/isda-overlap.md`.
  - Initialise the live-run corroboration ledger (1015 UNVERIFIED rows) so G6
    can be evaluated; keep the `glm-5.2` exclusion after an unsuccessful retry.
- Rebuild release manifest to bind new specs, schemas, cells and documentation.
- All changes remain above the SPEC-03 floor: definitions, schemas, rubrics and
  public citations only. No institution instances, corpus material or workflow
  claims are included.

## v0.4.0 — 2026-09-08

- Add operating reference contract 1.0.0: public division/function/task/control-point identifiers and a schema for private, dated operating-unit registers.
- Derive and verify the reference catalogue from existing matrix/cell bytes; preserve the grid's model-consensus and curation limits.
- Bind the new contract, schema and catalogue into the release manifest. Require catalogue reproduction before release.
- Include the canonical entity semantics and CI conftest repair already merged since v0.3.0.

The public release contains definitions only. It does not contain institutional desks, local settings, private evidence or a compliance attestation. Existing division keys and control-point cells are preserved.
