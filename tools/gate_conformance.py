#!/usr/bin/env python3
"""SPEC-03 runnable gates: S3-G1..G4. Exit non-zero on any failure."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import yaml

from build_release_manifest import build_manifest, canonical_json, sha256_bytes

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []
SCHEMA_FIXTURES = {
    "specs/bocg-release-manifest.schema.json": [
        "reference/release-snapshots/v0.6.3/bocg-release-manifest.json",
    ],
    "specs/compliance-scenario.schema.json": [
        "specs/fixtures/compliance-scenario-synthetic.json",
    ],
    "specs/control-point-cell.schema.json": [
        "cells/cp_cftc_part43_realtime.json",
    ],
    "specs/episode-surface.schema.json": [
        "specs/fixtures/episode-surface-synthetic.json",
    ],
    "specs/financial-work-context.schema.json": [
        "reference/financial-work-context.v1.json",
    ],
    "specs/financial-work-placement.schema.json": [
        "specs/fixtures/financial-work-placement-synthetic.json",
    ],
    "specs/insight-construction.schema.json": [
        "specs/fixtures/insight-construction-synthetic.json",
    ],
    "specs/institutional-speech-act.schema.json": [
        "specs/fixtures/institutional-speech-act-synthetic.json",
    ],
    "specs/operating-unit-register.schema.json": [
        "specs/fixtures/operating-unit-register-synthetic.json",
    ],
    "specs/public-eval-llmaj-prereg.schema.json": [
        "reference/public-eval-llmaj-prereg.v1.json",
    ],
    "specs/public-eval-llmaj.schema.json": [
        "reference/public-eval-llmaj-ledger.v1.json",
    ],
    "specs/public-eval-observatory.schema.json": [
        "reference/public-eval-observatory.v1.json",
    ],
    "specs/public-eval-surface-overlay.schema.json": [
        "reference/public-eval-surface-map.v1.json",
    ],
    "specs/replayable-compliance-scenario.schema.json": [
        "specs/fixtures/replayable-compliance-scenario-synthetic.json",
    ],
    "specs/scenario-run-ledger-rows.schema.json": [
        "specs/scenario-run-ledger.example.json",
    ],
    "specs/scenario-run-ledger.schema.json": [
        "specs/fixtures/scenario-run-ledger-synthetic.json",
    ],
    "specs/task-concepts.schema.json": [
        "reference/task-concepts.v1.json",
    ],
}
# S3-G4: statused rows committed in CONFORMANCE.md. The gate fails on fewer
# rows (a row was dropped) and on more (raise this in the change that adds one).
CONFORMANCE_ROW_BASELINE = 19
# S3-G3: pinned paths the deny scan leaves alone. Run directories hold raw and
# derived model output published as recorded (I4); snapshots are historical bytes.
DENY_SCAN_EXEMPT_PREFIXES = ("live-run-", "reference/release-snapshots/")
# S3-G5: the tier bocg/bocg/grid.py writes to grid.json for a division that
# dropped below admission once refuted anchors were removed (SPEC-01 section 6).
REJECTED_TIER = "REJECTED_POST_CORROBORATION"
REJECTED_BY_RUN: dict[str, set[str]] = {}   # run directory -> keys rejected in its grid.json


def fail(msg: str) -> None:
    FAILURES.append(msg)


def _rejected_after_corroboration(run: Path, keys: set[str], *, required: bool) -> set[str]:
    """SPEC-01 section 6: keys whose tier in the run's grid.json is REJECTED_POST_CORROBORATION.

    A rejection exists only once a ledger has been corroborated. The
    taxonomy-source run must carry a readable grid.json covering every matrix
    key as soon as it has a corroboration ledger; a run with no ledger, and a
    historical run recorded without a grid file, fall back to matrix.csv alone.
    A grid file that is present is always read.
    """
    if not (run / "grid.json").exists():
        if required and (run / "corroboration.csv").exists():
            raise ValueError("corroboration.csv exists but grid.json is missing, so admission after corroboration cannot be read")
        return set()
    grid_path = (run / "grid.json").resolve(strict=True)
    if not grid_path.is_relative_to(run):
        raise ValueError("grid.json resolves outside its taxonomy run")
    grid = json.loads(grid_path.read_text(encoding="utf-8"))
    cells = grid.get("cells") if isinstance(grid, dict) else None
    if not isinstance(cells, list):
        raise ValueError("grid.json has no cells list")
    tiers: dict[str, str] = {}
    for index, cell in enumerate(cells):
        key = cell.get("division_key") if isinstance(cell, dict) else None
        if not isinstance(key, str) or not isinstance(cell.get("tier"), str) or key in tiers:
            raise ValueError(f"grid.json cell {index} has an invalid or duplicate division_key or tier")
        tiers[key] = cell["tier"]
    if keys - set(tiers):
        raise ValueError(f"grid.json does not cover matrix.csv keys {sorted(keys - set(tiers))}")
    return {key for key, tier in tiers.items() if tier == REJECTED_TIER}


def _rejection_note(key: object, run_dir: str) -> str:
    rejected = isinstance(key, str) and key in REJECTED_BY_RUN.get(run_dir, set())
    return f" ({REJECTED_TIER} in grid.json)" if rejected else ""


def _admitted_division_keys(
    run_dir: str | None = None, *, context: str = "taxonomy source"
) -> tuple[set[str] | None, str]:
    """S3-G5: read admitted keys from the named, repository-local taxonomy run.

    A key is admitted when matrix.csv lists it and grid.json does not record
    it as rejected after corroboration.
    """
    is_source_run = run_dir is None
    if run_dir is None:
        try:
            source = json.loads((ROOT / "reference/taxonomy-source.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            fail(f"S3-G5 {context}: taxonomy source is unreadable ({exc})")
            return None, ""
        if not isinstance(source, dict):
            fail(f"S3-G5 {context}: taxonomy source must be a JSON object")
            return None, ""
        run_dir = source.get("run_dir")
    if not isinstance(run_dir, str) or not re.fullmatch(r"live-run-[0-9]{8}", run_dir):
        fail(f"S3-G5 {context}: taxonomy run must be a repository-local live-run-YYYYMMDD directory")
        return None, ""
    try:
        root = ROOT.resolve(strict=True)
        run = (ROOT / run_dir).resolve(strict=True)
        if not run.is_relative_to(root):
            raise ValueError("taxonomy run resolves outside the repository")
        if not run.is_dir():
            raise ValueError("unknown taxonomy run directory")
        matrix_path = (run / "matrix.csv").resolve(strict=True)
        if not matrix_path.is_relative_to(run):
            raise ValueError("matrix.csv resolves outside its taxonomy run")
        with matrix_path.open(encoding="utf-8", newline="") as handle:
            rows = csv.DictReader(handle, strict=True)
            fields = rows.fieldnames or []
            if len(fields) != len(set(fields)) or not {"division_key", "model_support", "tier"} <= set(fields):
                raise ValueError("matrix.csv has missing or duplicate header fields")
            keys: set[str] = set()
            for index, row in enumerate(rows, 2):
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f"matrix.csv row {index} has the wrong number of fields")
                key = row["division_key"]
                if not re.fullmatch(r"[a-z0-9_]+", key) or key in keys:
                    raise ValueError(f"matrix.csv row {index} has an invalid or duplicate division_key")
                if not row["model_support"].isdigit() or row["tier"] not in {"WEAK", "MODERATE", "STRONG"}:
                    raise ValueError(f"matrix.csv row {index} has invalid admission metadata")
                keys.add(key)
        if not keys:
            raise ValueError("matrix.csv contains no admitted division keys")
        rejected = _rejected_after_corroboration(run, keys, required=is_source_run)
    except FileNotFoundError as exc:
        fail(f"S3-G5 {context}: unknown taxonomy run or missing matrix.csv ({exc})")
        return None, ""
    except (OSError, ValueError, csv.Error, RuntimeError) as exc:
        fail(f"S3-G5 {context}: taxonomy run, matrix.csv or grid.json is invalid ({exc})")
        return None, ""
    REJECTED_BY_RUN[run_dir] = rejected
    return keys - rejected, run_dir


def gate_cells() -> None:
    """S3-G1 citations, S3-G2 consequence anchors, schema validity, S3-G5 admitted keys."""
    try:
        import jsonschema
    except ImportError:
        fail("S3-G1 jsonschema is required to validate control-point cells")
        return
    try:
        schema = json.loads((ROOT / "specs/control-point-cell.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    except (OSError, ValueError, jsonschema.exceptions.SchemaError) as exc:
        fail(f"S3-G1 control-point schema is unreadable or invalid ({str(exc)[:120]})")
        return
    admitted, run_dir = _admitted_division_keys()
    for path in sorted((ROOT / "cells").glob("*.json")):
        try:
            cell = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            fail(f"S3-G1 {path.name}: unreadable or invalid JSON ({exc})")
            continue
        if not isinstance(cell, dict):
            fail(f"S3-G1 {path.name}: cell must be a JSON object")
            continue
        schema_errors = list(validator.iter_errors(cell))
        for err in schema_errors:
            fail(f"S3-G1 {path.name}: schema: {err.message[:120]}")
        if schema_errors:
            continue
        for i, cit in enumerate(cell.get("citations") or []):
            if not str(cit.get("url", "")).startswith("http"):
                fail(f"S3-G1 {path.name}: citation {i} has no URL")
        anchor = cell.get("consequence_anchor") or {}
        if not anchor.get("public_source"):
            fail(f"S3-G2 {path.name}: consequence anchor lacks public_source")
        if re.search(r"\d+\.\d{3,}", str(anchor.get("magnitude_band", ""))):
            fail(f"S3-G2 {path.name}: magnitude_band has invented precision")
        if cell.get("status") != "RETIRED":
            key = cell.get("division_key")
            if admitted is not None and key not in admitted:
                fail(
                    f"S3-G5 {path.name}: division_key {key!r} is not admitted in {run_dir}"
                    f"{_rejection_note(key, run_dir)}"
                )
        for i, hist in enumerate(cell.get("division_key_history") or []):
            if hist.get("division_key") == cell.get("division_key"):
                fail(f"S3-G5 {path.name}: history {i} repeats the current division_key")
            historical, history_run = _admitted_division_keys(
                hist["taxonomy_run"], context=f"{path.name}: history {i}"
            )
            if historical is not None:
                was_admitted = hist["division_key"] in historical
                claimed_admitted = hist.get("admission_status", "ADMITTED") == "ADMITTED"
                if claimed_admitted and not was_admitted:
                    fail(
                        f"S3-G5 {path.name}: history {i} division_key {hist['division_key']!r} "
                        f"is not admitted in {history_run}"
                        f"{_rejection_note(hist['division_key'], history_run)}"
                    )
                elif not claimed_admitted and was_admitted:
                    fail(
                        f"S3-G5 {path.name}: history {i} claims UNADMITTED but division_key "
                        f"{hist['division_key']!r} is admitted in {history_run}"
                    )


def _taxonomy_source_run(label: str) -> tuple[Path | None, str]:
    """Resolve the repository-local run named by reference/taxonomy-source.json."""
    try:
        source = json.loads((ROOT / "reference/taxonomy-source.json").read_text(encoding="utf-8"))
        run_dir = source.get("run_dir") if isinstance(source, dict) else None
        if not isinstance(run_dir, str) or not re.fullmatch(r"live-run-[0-9]{8}", run_dir):
            raise ValueError("run_dir must name a repository-local live-run-YYYYMMDD directory")
        run = (ROOT / run_dir).resolve(strict=True)
        if not run.is_relative_to(ROOT.resolve(strict=True)) or not run.is_dir():
            raise ValueError("run directory resolves outside the repository or is not a directory")
    except (OSError, ValueError, RuntimeError) as exc:
        fail(f"{label}: taxonomy source run is missing or unreadable ({exc})")
        return None, ""
    return run, run_dir


def gate_run_summary() -> None:
    """RUN_SUMMARY.json of the taxonomy-source run agrees with its gate report and ledger.

    Only the run named by reference/taxonomy-source.json is checked. The
    summary of a historical run stays as it was written.
    """
    run, run_dir = _taxonomy_source_run("RUN-SUMMARY")
    if run is None:
        return
    label = f"RUN-SUMMARY {run_dir}"
    try:
        summary = json.loads((run / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
        report = json.loads((run / "gates_report.json").read_text(encoding="utf-8"))
        if not isinstance(summary, dict) or not isinstance(report, dict):
            raise ValueError("RUN_SUMMARY.json and gates_report.json must be JSON objects")
        executed: dict[str, str] = {}
        for gate in report["gates"]:
            if gate["id"] in executed:
                raise ValueError(f"gates_report.json repeats gate {gate['id']!r}")
            executed[gate["id"]] = gate["status"]
        with (run / "corroboration.csv").open(encoding="utf-8", newline="") as handle:
            rows = csv.DictReader(handle, strict=True)
            if "status" not in (rows.fieldnames or []):
                raise ValueError("corroboration.csv has no status column")
            ledger: list[str] = []
            for index, row in enumerate(rows, 2):
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f"corroboration.csv row {index} has the wrong number of fields")
                ledger.append(row["status"])
    except (OSError, ValueError, csv.Error, KeyError, TypeError) as exc:
        fail(f"{label}: run summary, gate report or ledger is missing or unreadable ({exc!r})")
        return
    claimed = summary.get("gates")
    if not isinstance(claimed, dict):
        fail(f"{label}: RUN_SUMMARY.json has no gates object")
    else:
        for gate_id in [*executed, *(g for g in claimed if g not in executed)]:
            if claimed.get(gate_id) != executed.get(gate_id):
                fail(
                    f"{label}: gate {gate_id} is {claimed.get(gate_id)!r} in RUN_SUMMARY.json "
                    f"but {executed.get(gate_id)!r} in gates_report.json"
                )
    stamp = summary.get("gates_executed_at")
    if stamp is not None and stamp != report.get("ts_utc"):
        fail(f"{label}: gates_executed_at {stamp!r} is not the gate report's ts_utc {report.get('ts_utc')!r}")
    counted: dict[str, int] = {}
    for status in ledger:
        counted[status] = counted.get(status, 0) + 1
    held = ", ".join(f"{count} {status}" for status, count in sorted(counted.items()))
    totals = summary.get("corroboration")
    by_status = totals.get("by_status") if isinstance(totals, dict) else None
    if not isinstance(by_status, dict):
        fail(
            f"{label}: RUN_SUMMARY.json has no corroboration totals block "
            f"(corroboration.csv holds {held} of {len(ledger)} rows)"
        )
        return
    rows_claimed = totals.get("ledger_rows")
    if type(rows_claimed) is not int or rows_claimed != len(ledger):
        fail(f"{label}: corroboration.ledger_rows is {rows_claimed!r} but corroboration.csv holds {len(ledger)} rows")
    for status in sorted(set(by_status) | set(counted)):
        count = by_status.get(status, 0)
        if type(count) is not int or count != counted.get(status, 0):
            fail(
                f"{label}: corroboration.by_status.{status} is {by_status.get(status)!r} "
                f"but corroboration.csv holds {counted.get(status, 0)} such rows"
            )


def gate_deny() -> int:
    """S3-G3: forbidden tokens in every artifact a release would pin.

    Run directories are not scanned: raw and derived model output is published
    as recorded under I4. Retained release snapshots are historical bytes.
    Returns the number of files scanned.
    """
    literals, patterns = [], []
    sources = [ROOT / "tools/forbidden_cells.txt"]
    local = ROOT / "tools/forbidden_cells.local.txt"   # untracked seller list
    if local.is_file():
        sources.append(local)
    for source in sources:
        for line in source.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("regex:"):
                patterns.append(re.compile(line[6:], re.I))
            else:
                literals.append(line.lower())
    targets = list((ROOT / "cells").glob("*.json")) + [
        ROOT / "specs/SPEC-03-control-point-cells.md",
        ROOT / "specs/SPEC-04-common-semantic-profile.md",
        ROOT / "specs/common-semantic-profile.yaml",
        # S8-G5: the same deny list covers the concept layer and its fixture.
        ROOT / "specs/SPEC-08-task-concepts-and-episode-surface.md",
        ROOT / "reference/task-concept-rulings.yaml",
        ROOT / "reference/task-concepts.v1.json",
        ROOT / "specs/fixtures/episode-surface-synthetic.json",
        # S9-G4: public-eval overlay stays above the SPEC-03 floor.
        ROOT / "specs/SPEC-09-public-eval-surface-overlay.md",
        ROOT / "reference/public-eval-inventory.v1.yaml",
        ROOT / "reference/public-eval-surface-map.v1.json",
        ROOT / "reference/public-eval-llmaj-ledger.v1.json",
        ROOT / "reference/public-eval-llmaj-prereg.v1.json",
        ROOT / "reference/public-eval-observatory.v1.json",
        ROOT / "reference/cleanroom-eval-companion.v1.json",
        ROOT / "specs/public-eval-observatory.schema.json",
        ROOT / "specs/rubrics/public-eval-mapping.yaml",
        ROOT / "specs/prompts/public-eval-llmaj-judge.v1.txt",
        ROOT / "specs/fixtures/public-eval-llmaj-synthetic.json",
    ]
    # The hand list above stays as a floor. The pinned set is what ships, so
    # an artifact added to a release is scanned without being listed here.
    try:
        pinned = build_manifest(
            tag="v0.0.0-gate", commit_sha="0" * 40, generated_at="2000-01-01T00:00:00Z", root=ROOT
        )["artifacts"]
    except (OSError, ValueError) as exc:
        fail(f"S3-G3 pinned artifacts cannot be listed for the deny scan: {exc}")
        pinned = []
    scanned = {path.relative_to(ROOT).as_posix(): path for path in targets}
    for row in pinned:
        relative = row["path"]
        if not relative.startswith(DENY_SCAN_EXEMPT_PREFIXES):
            scanned.setdefault(relative, ROOT / relative)
    for relative, path in scanned.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        for token in literals:
            if token in lowered:
                fail(f"S3-G3 {relative}: forbidden token (from deny list)")
        for pattern in patterns:
            if pattern.search(text):
                fail(f"S3-G3 {relative}: forbidden pattern {pattern.pattern!r}")
    return len(scanned)


def gate_conformance_doc() -> None:
    """S3-G4: CONFORMANCE.md rows intact and statused."""
    doc = (ROOT / "CONFORMANCE.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d+) \| .+ \| (EVIDENCED|PARTIAL|NOT MET) \|", doc, re.M)
    if len(rows) < CONFORMANCE_ROW_BASELINE:
        fail(
            f"S3-G4 CONFORMANCE.md: {len(rows)} statused rows found, baseline is "
            f"{CONFORMANCE_ROW_BASELINE} (a row was dropped)"
        )
    elif len(rows) > CONFORMANCE_ROW_BASELINE:
        fail(
            f"S3-G4 CONFORMANCE.md: {len(rows)} statused rows found, baseline is "
            f"{CONFORMANCE_ROW_BASELINE} (a row was added without raising "
            f"CONFORMANCE_ROW_BASELINE in the same change)"
        )
    numbers = [int(r[0]) for r in rows]
    if numbers != list(range(1, len(numbers) + 1)):
        fail("S3-G4 CONFORMANCE.md: row numbering broken (row removed or reordered)")


def _schema_pointer_exists(schema: dict, pointer: str) -> bool:
    prefix = "control-point-cell.schema.json#"
    if not pointer.startswith(prefix):
        return False
    value: object = schema
    for part in pointer[len(prefix):].strip("/").split("/"):
        if not part:
            continue
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return True


def gate_common_semantics() -> None:
    """S4: portable mappings reuse existing schemas and stop above workflow."""
    profile_path = ROOT / "specs/common-semantic-profile.yaml"
    schema = json.loads((ROOT / "specs/control-point-cell.schema.json").read_text())
    try:
        profile = yaml.safe_load(profile_path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        fail(f"S4-G1 common semantic profile is unreadable: {exc}")
        return
    try:
        proposed_context = json.loads(
            (ROOT / "reference/financial-work-context-proposals.v1.json").read_text(encoding="utf-8")
        )
        context = json.loads(
            (ROOT / "reference/financial-work-context.v1.json").read_text(encoding="utf-8")
        )
        operating_contract = json.loads(
            (ROOT / "specs/operating-reference-contract.json").read_text(encoding="utf-8")
        )
        context_version = proposed_context["version"]
        declared_versions = {
            "proposal": context_version,
            "catalogue": context["version"],
            "operating-reference contract": operating_contract["optional_context"]["version"],
            "common semantic profile": (profile.get("financial_work_context") or {}).get("version"),
        }
        if any(version != context_version for version in declared_versions.values()):
            fail(f"S10-G1 financial work-context versions disagree: {declared_versions}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        fail(f"S10-G1 financial work-context version source is unreadable: {exc}")
    meta = profile.get("profile") or {}
    if meta.get("id") != "bocg-common-semantics" or meta.get("scope", {}).get("ceiling") != "control_point":
        fail("S4-G1 profile identity or control-point ceiling drifted")
    if meta.get("scope", {}).get("occurrence_claims_permitted") is not False:
        fail("S4-G1 occurrence claims must remain prohibited")
    prohibited = set(meta.get("prohibited_object_types") or [])
    required_prohibited = {"ObservationAtom", "Trace", "Episode", "EmailDiscourseBlock", "FiveFamilyAssessment"}
    if not required_prohibited.issubset(prohibited):
        fail("S4-G1 below-floor object deny list is incomplete")

    standards = profile.get("standards") or {}
    for authority, row in standards.items():
        if not isinstance(row, dict) or not str(row.get("uri") or "").startswith("https://"):
            fail(f"S4-G2 standard {authority}: HTTPS URI required")
        if not row.get("label") or not row.get("authority") or not row.get("use"):
            fail(f"S4-G2 standard {authority}: label, authority and use required")
    allowed = set((profile.get("mapping_policy") or {}).get("allowed_relations") or [])
    if not allowed or (profile.get("mapping_policy") or {}).get("mapping_is_not_identity") is not True:
        fail("S4-G2 mapping strengths or non-identity policy missing")
    entities = profile.get("entity_semantics") or {}
    if entities.get("id") != "bocg-canonical-entities":
        fail("S4-G6 canonical entity semantics missing")
    for field in ("corpus_membership_is_identity", "label_equality_is_identity", "type_mapping_is_instance_identity"):
        if entities.get(field) is not False:
            fail(f"S4-G6 {field} must be false")
    for name, definition in entities.get("classes", {}).items():
        if (definition.get("standard") not in standards
                or not str(definition.get("term", "")).startswith(("http://", "https://"))
                or definition.get("relation") not in allowed or not definition.get("identity")):
            fail(f"S4-G6 {name} lacks standards-bearing semantics or identity rule")
    if not {"person", "organization", "account", "instrument", "product_type", "system", "role"} <= set(entities.get("classes", {})):
        fail("S4-G6 business entity classes incomplete")
    products = entities.get("product_classification") or {}
    if set(products.get("reference_key", [])) != {"authority", "regime", "identifier", "version", "valid_from", "valid_to"}:
        fail("S4-G6 product reference must bind authority, regime, version and validity")
    relationships = entities.get("contextual_relationships") or {}
    for field in ("observation_time_is_not_validity_time", "unknown_validity_bounds_remain_unknown",
                  "facing_direction_is_not_symmetric", "facing_role_is_not_intrinsic_to_organization"):
        if relationships.get(field) is not True:
            fail(f"S4-G6 contextual relationship invariant missing: {field}")

    def check_mappings(location: str, mappings: object) -> None:
        if not isinstance(mappings, list) or not mappings:
            fail(f"S4-G2 {location}: at least one mapping required")
            return
        for index, row in enumerate(mappings):
            if not isinstance(row, dict):
                fail(f"S4-G2 {location}[{index}]: mapping must be an object")
                continue
            if row.get("authority") not in standards:
                fail(f"S4-G2 {location}[{index}]: undeclared authority")
            if row.get("relation") not in allowed:
                fail(f"S4-G2 {location}[{index}]: prohibited mapping relation")
            if not row.get("term"):
                fail(f"S4-G2 {location}[{index}]: mapped term required")

    for object_id, row in (profile.get("semantic_objects") or {}).items():
        check_mappings(f"semantic_objects.{object_id}", (row or {}).get("mappings"))
    field_mappings = profile.get("field_mappings") or {}
    for pointer, mappings in field_mappings.items():
        if not _schema_pointer_exists(schema, pointer):
            fail(f"S4-G3 field mapping does not resolve existing schema path: {pointer}")
        check_mappings(f"field_mappings.{pointer}", mappings)
    required_fields = set(schema.get("required") or [])
    mapped_fields = {
        pointer.split("/properties/", 1)[1].split("/", 1)[0]
        for pointer in field_mappings
        if "/properties/" in pointer
    }
    if required_fields - mapped_fields:
        fail(f"S4-G3 required SPEC-03 fields lack mappings: {sorted(required_fields - mapped_fields)}")
    for relation_id, row in (profile.get("relation_vocabulary") or {}).items():
        if (row or {}).get("domain") not in (profile.get("semantic_objects") or {}):
            fail(f"S4-G4 relation {relation_id}: unknown domain")
        if (row or {}).get("range") not in (profile.get("semantic_objects") or {}):
            fail(f"S4-G4 relation {relation_id}: unknown range")
        check_mappings(f"relation_vocabulary.{relation_id}", (row or {}).get("mappings"))


def gate_release_manifest() -> None:
    """S4-G5: a release can publish one self-consistent hash manifest."""
    try:
        manifest = build_manifest(
            tag="v0.0.0-gate",
            commit_sha="0" * 40,
            generated_at="2000-01-01T00:00:00Z",
        )
        schema = json.loads(
            (ROOT / "specs/bocg-release-manifest.schema.json").read_text()
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail(f"S4-G5 release manifest cannot be built: {exc}")
        return
    try:
        import jsonschema

        for error in jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).iter_errors(manifest):
            fail(f"S4-G5 release manifest schema: {error.message[:120]}")
    except ImportError:
        pass
    artifacts = manifest.get("artifacts") or []
    if [row.get("path") for row in artifacts] != sorted(
        row.get("path") for row in artifacts
    ):
        fail("S4-G5 release artifacts are not deterministically ordered")
    if manifest.get("aggregate_sha256") != sha256_bytes(canonical_json(artifacts)):
        fail("S4-G5 aggregate artifact digest is invalid")
    claimed = manifest.pop("manifest_sha256", None)
    if claimed != sha256_bytes(canonical_json(manifest)):
        fail("S4-G5 manifest self-digest is invalid")


def gate_insight_construction() -> None:
    """S5: portable occurrence shapes remain static and lifecycle-safe."""
    profile_path = ROOT / "specs/insight-construction-profile.yaml"
    try:
        profile = yaml.safe_load(profile_path.read_text())
        insight_schema = json.loads((ROOT / "specs/insight-construction.schema.json").read_text())
        speech_schema = json.loads((ROOT / "specs/institutional-speech-act.schema.json").read_text())
        episode = yaml.safe_load((ROOT / "specs/rubrics/episode-feasibility.yaml").read_text())
        families = yaml.safe_load((ROOT / "specs/rubrics/five-families.yaml").read_text())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        fail(f"S5-G1 insight-construction artifacts unreadable: {exc}")
        return
    meta = profile.get("profile") or {}
    scope = meta.get("scope") or {}
    if meta.get("id") != "bocg-insight-construction" or meta.get("layered_on") != "bocg-common-semantics":
        fail("S5-G1 layered profile identity drifted")
    if scope.get("definitions_only") is not True or scope.get("occurrence_instances_permitted") is not False:
        fail("S5-G1 profile must publish definitions but no occurrence instances")
    lifecycle = profile.get("lifecycle_vocabulary") or {}
    required = {"directed", "scheduled", "executed", "completed", "verified"}
    if not required.issubset(set(lifecycle.get("ordered_states") or [])):
        fail("S5-G2 lifecycle state separation is incomplete")
    rules = lifecycle.get("inference_rules") or {}
    if any(rules.get(key) is not False for key in (
        "directive_implies_execution", "scheduled_implies_execution",
        "executed_implies_completion", "completed_implies_verification",
    )):
        fail("S5-G2 lifecycle inference must fail closed")
    if not {"ObservationAtom", "Trace", "Episode"}.issubset((insight_schema.get("$defs") or {}).keys()):
        fail("S5-G3 insight schema lacks Atom/Trace/Episode definitions")
    obligation = ((speech_schema.get("properties") or {}).get("obligation_frame") or {}).get("properties") or {}
    if "executed" in ((obligation.get("execution_status") or {}).get("enum") or []):
        fail("S5-G3 directive expansion must not assert execution")
    if (episode.get("rubric") or {}).get("safeguards", {}).get("atom_truth_does_not_imply_episode_truth") is not True:
        fail("S5-G4 Episode rubric lacks composition safeguard")
    family_ids = set(((families.get("rubric") or {}).get("families") or {}).keys())
    if family_ids != {"DEEP_DOMAIN_TRANSFER", "EVIDENCE_ABLATION", "NEGATIVE_CONTROL", "LATERAL_HIRE", "COMMERCIAL_INSIGHT"}:
        fail("S5-G5 Five Families vocabulary drifted")


def gate_worked_sample_calendar() -> None:
    """S5-G6: published worked-sample dates resolve to covered business days."""
    from calendar_gate import validate_calendar_data, validate_dated_sample

    calendar_path = ROOT / "reference/business-calendars.v1.json"
    try:
        calendar_data = json.loads(calendar_path.read_text(encoding="utf-8"))
        profile = yaml.safe_load(
            (ROOT / "specs/insight-construction-profile.yaml").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        fail(f"S5-G6 calendar data or profile is unreadable: {exc}")
        return
    for error in validate_calendar_data(calendar_data):
        fail(f"S5-G6 {error}")
    expected_calendars = set(
        (
            ((profile.get("lifecycle_vocabulary") or {}).get("temporal_semantics") or {})
            .get("calendar_ref", {})
            .get("examples", [])
        )
    )
    actual_calendars = set(
        (calendar_data.get("calendars") or {}).keys()
        if isinstance(calendar_data, dict) and isinstance(calendar_data.get("calendars"), dict)
        else ()
    )
    if expected_calendars - actual_calendars:
        fail(f"S5-G6 missing example calendars {sorted(expected_calendars - actual_calendars)}")
    sample_paths = sorted((ROOT / "reference/worked-samples").glob("*.json"))
    if not sample_paths:
        fail("S5-G6 no published dated samples found")
        return
    found_r3 = False
    for sample_path in sample_paths:
        try:
            sample = json.loads(sample_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            fail(f"S5-G6 {sample_path.name} is unreadable: {exc}")
            continue
        if not isinstance(sample, dict):
            fail(f"S5-G6 {sample_path.name} is not an object")
            continue
        if sample.get("sample_id") == "FM-PB-0417" and sample.get("revision") == "R3":
            found_r3 = True
        if sample.get("publication_status") != "published":
            fail(f"S5-G6 {sample_path.name} is not marked published")
        for error in validate_dated_sample(sample, calendar_data):
            fail(f"S5-G6 {sample_path.name}: {error}")
    if not found_r3:
        fail("S5-G6 published worked sample FM-PB-0417-R3 is missing")


def gate_compliance_scenarios() -> str | None:
    """S7: replayable compliance scenarios are schema-valid, pinned and lifecycle-safe.

    Returns the pinned cell and its status in the pinned release, for the
    success line. The status is reported, not gated.
    """
    try:
        import jsonschema
        from release_snapshots import (
            ReleaseSnapshotError, load_release_artifact, load_release_manifest,
            read_json_object, required_format_checker, validate_manifest,
        )
    except ImportError as exc:
        fail(f"S7-G1 required validation dependency is unavailable: {exc}")
        return
    schema_path = ROOT / "specs/compliance-scenario.schema.json"
    fixture_path = ROOT / "specs/fixtures/compliance-scenario-synthetic.json"
    manifest_path = ROOT / "bocg-release-manifest.json"
    try:
        schema = read_json_object(schema_path)
        fixture = read_json_object(fixture_path)
        format_checker = required_format_checker()
    except (OSError, UnicodeError, ValueError) as exc:
        fail(f"S7-G1 compliance-scenario artifacts unreadable: {exc}")
        return
    errors = list(jsonschema.Draft202012Validator(
        schema, format_checker=format_checker
    ).iter_errors(fixture))
    if errors:
        for err in errors:
            fail(f"S7-G1 fixture schema: {err.message[:120]}")
        return
    # An absent embedded manifest is normal in a source checkout. A present
    # malformed manifest is never absence, and a pin must always resolve to a
    # verified snapshot (or an explicitly digest-pinned local manifest).
    if manifest_path.exists():
        try:
            validate_manifest(read_json_object(manifest_path), root=ROOT)
        except (OSError, UnicodeError, ValueError) as exc:
            fail(f"S7-G5 local release manifest is invalid: {exc}")
            return
    pinned_sha256 = fixture["manifest_sha256"]
    try:
        load_release_manifest(ROOT, manifest_sha256=pinned_sha256)
        cell_id = fixture["cell_id"]
        cell = json.loads(load_release_artifact(
            ROOT, f"cells/{cell_id}.json", manifest_sha256=pinned_sha256
        ))
        if not isinstance(cell, dict) or cell.get("cell_id") != cell_id:
            raise ReleaseSnapshotError("referenced cell identity differs from its release artifact")
        catalogue = json.loads(load_release_artifact(
            ROOT, "reference/operating-catalogue.v1.json", manifest_sha256=pinned_sha256
        ))
        if not any(d.get("kind") == "task" and d.get("reference_id") == fixture["task_ref"]
                   for d in catalogue.get("definitions", [])):
            raise ReleaseSnapshotError("task_ref is not a task in the pinned release")
    except (ReleaseSnapshotError, ValueError, TypeError, AttributeError) as exc:
        fail(f"S7-G2 scenario release binding is invalid: {exc}")
        return
    expected = fixture.get("expected_verdict") or {}
    if expected.get("directive_may_satisfy_execution") is not False:
        fail("S7-G3 expected_verdict must fail closed: directive never satisfies execution")
    pass_rule = fixture.get("pass_rule") or {}
    if pass_rule.get("is_boolean") is not False:
        fail("S7-G3 pass_rule must be statistical, never boolean")
    controls = set((fixture.get("controls") or {}).get("five_families_checks") or [])
    if not {"NEGATIVE_CONTROL", "EVIDENCE_ABLATION"} <= controls:
        fail("S7-G4 controls must include NEGATIVE_CONTROL and EVIDENCE_ABLATION")
    return f"{cell_id} at status {cell.get('status')}"


def gate_replayable_compliance_scenario() -> None:
    """S7: current replayable scenario hashes and release references resolve."""
    try:
        import jsonschema
        from release_snapshots import (
            ReleaseSnapshotError, load_release_artifact, load_release_manifest,
            read_json_object, required_format_checker,
        )
        schema = read_json_object(ROOT / "specs/replayable-compliance-scenario.schema.json")
        fixture = read_json_object(
            ROOT / "specs/fixtures/replayable-compliance-scenario-synthetic.json"
        )
        format_checker = required_format_checker()
    except (ImportError, OSError, UnicodeError, ValueError) as exc:
        fail(f"S7-G5 replayable scenario artifacts unreadable: {exc}")
        return
    errors = list(jsonschema.Draft202012Validator(
        schema, format_checker=format_checker
    ).iter_errors(fixture))
    for err in errors:
        fail(f"S7-G5 replayable scenario schema: {err.message[:120]}")
    if errors:
        return
    try:
        release = fixture["bocg_release"]
        load_release_manifest(
            ROOT, release_tag=release["release_tag"],
            manifest_sha256=release["manifest_sha256"],
        )
        cell_id = fixture["cell_ref"]["cell_id"]
        cell_bytes = load_release_artifact(
            ROOT, f"cells/{cell_id}.json", manifest_sha256=release["manifest_sha256"]
        )
        if sha256_bytes(cell_bytes) != fixture["cell_ref"]["cell_sha256"]:
            raise ReleaseSnapshotError("cell_ref.cell_sha256 does not match pinned raw artifact bytes")
        catalogue = json.loads(load_release_artifact(
            ROOT, "reference/operating-catalogue.v1.json",
            manifest_sha256=release["manifest_sha256"],
        ))
        task_ref = fixture["task_ref"]
        if not any(
            definition.get("kind") == "task"
            and definition.get("division_key") == task_ref["division_key"]
            and definition.get("reference_id") == task_ref["reference_id"]
            for definition in catalogue.get("definitions", [])
        ):
            raise ReleaseSnapshotError("task_ref is not a task in the pinned release")
    except (ReleaseSnapshotError, ValueError, TypeError, KeyError) as exc:
        fail(f"S7-G5 replayable scenario release binding is invalid: {exc}")
        return
    hashed_fields = (
        "cell_ref", "task_ref", "input_state", "oracle", "expected_verdict"
    )
    body = {key: fixture[key] for key in hashed_fields}
    if fixture["scenario_hash"] != sha256_bytes(canonical_json(body)):
        fail("S7-G5 scenario_hash does not match canonical JSON of its declared hash fields")


def gate_schema_fixtures() -> None:
    """Every published JSON schema has a unique identity and a validated fixture."""
    import jsonschema

    schemas = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "specs").rglob("*.schema.json")
    }
    mapped = set(SCHEMA_FIXTURES)
    for missing in sorted(schemas - mapped):
        fail(f"schema fixture gate has no fixture mapping: {missing}")
    for unknown in sorted(mapped - schemas):
        fail(f"schema fixture gate refers to unknown schema: {unknown}")
    ids: dict[str, str] = {}
    schema_ids: dict[str, str] = {}
    for relative in sorted(schemas & mapped):
        try:
            schema = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
        except (OSError, UnicodeError, ValueError, jsonschema.SchemaError) as exc:
            fail(f"schema fixture gate cannot load schema {relative}: {exc}")
            continue
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            fail(f"schema fixture gate requires a nonempty $id: {relative}")
        elif schema_id in ids:
            fail(f"duplicate schema $id {schema_id}: {ids[schema_id]} and {relative}")
        else:
            ids[schema_id] = relative
        contract_id = (schema.get("properties") or {}).get("schema", {}).get("const")
        if isinstance(contract_id, str):
            if contract_id in schema_ids:
                fail(
                    f"duplicate schema contract identifier {contract_id}: "
                    f"{schema_ids[contract_id]} and {relative}"
                )
            else:
                schema_ids[contract_id] = relative
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )
        for fixture_path in SCHEMA_FIXTURES[relative]:
            try:
                fixture = json.loads((ROOT / fixture_path).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, ValueError) as exc:
                fail(f"schema fixture gate cannot load {fixture_path}: {exc}")
                continue
            for err in validator.iter_errors(fixture):
                fail(f"{fixture_path} against {relative}: {err.message[:120]}")


def gate_scenario_run_ledger() -> None:
    """S7: append-only scenario-run ledger schema, fixture and row integrity."""
    schema_path = ROOT / "specs/scenario-run-ledger-rows.schema.json"
    fixture_path = ROOT / "specs/scenario-run-ledger.example.json"
    try:
        schema = json.loads(schema_path.read_text())
        ledger = json.loads(fixture_path.read_text())
        scenario = json.loads(
            (ROOT / "specs/fixtures/replayable-compliance-scenario-synthetic.json").read_text()
        )
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"S7-G1 scenario-run ledger unreadable: {exc}")
        return
    try:
        import jsonschema
        validator = jsonschema.Draft202012Validator(schema)
    except ImportError:
        validator = None
    if validator:
        for err in validator.iter_errors(ledger):
            fail(f"S7-G1 fixture schema: {err.message[:120]}")
    if ledger.get("schema") != "bocg.scenario-run-ledger.v1":
        fail("S7-G1 ledger schema identity drifted")
    rows = ledger.get("rows") or []
    scenario_sha256 = sha256_bytes(canonical_json(scenario))
    scenario_release = scenario.get("bocg_release")
    manifest_sha256 = (
        scenario_release.get("manifest_sha256")
        if isinstance(scenario_release, dict)
        else None
    )
    seen_hashes = set()
    for i, row in enumerate(rows):
        claimed = row.get("row_sha256")
        body = {k: v for k, v in row.items() if k != "row_sha256"}
        computed = sha256_bytes(canonical_json(body))
        if claimed != computed:
            fail(f"S7-G2 row {i}: row_sha256 mismatch")
        if claimed in seen_hashes:
            fail(f"S7-G2 row {i}: duplicate row_sha256")
        seen_hashes.add(claimed)
        if row.get("manifest_sha256") != manifest_sha256:
            fail(f"S7-G2 row {i}: manifest_sha256 does not match the scenario release pin")
        if row.get("scenario_sha256") != scenario_sha256:
            fail(f"S7-G2 row {i}: scenario_sha256 does not match canonical scenario JSON")
        replaces = row.get("replaces_row_sha256")
        if replaces is not None and replaces not in seen_hashes:
            fail(f"S7-G2 row {i}: replaces_row_sha256 does not resolve to an earlier row")
    families = yaml.safe_load((ROOT / "specs/rubrics/five-families.yaml").read_text())
    allowed_verdicts = set((families.get("rubric") or {}).get("verdicts") or [])
    if not {"PASS", "FAIL", "UNCERTAIN", "NOT_APPLICABLE"}.issubset(allowed_verdicts):
        fail("S7-G3 five-families verdict vocabulary missing required values")
    for i, row in enumerate(rows):
        if row.get("verdict") not in allowed_verdicts:
            fail(f"S7-G3 row {i}: verdict not in five-families vocabulary")


def gate_task_concepts() -> None:
    """S8-G1..G4: concepts reproduce, partition the catalogue, declare provenance; surface fixture obeys the depth rule."""
    from build_task_concepts import build_task_concepts, render, KINDS
    from episode_surface import surface_problems
    try:
        concepts_path = ROOT / "reference/task-concepts.v1.json"
        concepts = json.loads(concepts_path.read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "specs/task-concepts.schema.json").read_text())
        surface_schema = json.loads((ROOT / "specs/episode-surface.schema.json").read_text())
        fixture = json.loads((ROOT / "specs/fixtures/episode-surface-synthetic.json").read_text())
        catalogue = json.loads((ROOT / "reference/operating-catalogue.v1.json").read_text())
        rulings = yaml.safe_load((ROOT / "reference/task-concept-rulings.yaml").read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        fail(f"S8-G1 task-concept artifacts unreadable: {exc}")
        return
    try:
        if render(build_task_concepts(ROOT)) != concepts_path.read_text(encoding="utf-8"):
            fail("S8-G1 task concepts do not reproduce from the catalogue and rulings")
    except ValueError as exc:
        fail(f"S8-G1 task concepts cannot be built: {exc}")
    try:
        import jsonschema
        checker = jsonschema.FormatChecker()
        for error in jsonschema.Draft202012Validator(schema, format_checker=checker).iter_errors(concepts):
            fail(f"S8-G1 task-concepts schema: {error.message[:120]}")
        jsonschema.Draft202012Validator.check_schema(surface_schema)
        for error in jsonschema.Draft202012Validator(surface_schema, format_checker=checker).iter_errors(fixture):
            fail(f"S8-G4 episode-surface fixture schema: {error.message[:120]}")
    except ImportError:
        pass
    released = {d["reference_id"]: d for d in catalogue["definitions"] if d["kind"] in KINDS}
    membership: list[str] = []
    for concept in concepts["concepts"]:
        for member in concept["members"]:
            definition = released.get(member)
            if definition is None or definition["division_key"] != concept["division_key"] or KINDS[definition["kind"]] != concept["kind"]:
                fail(f"S8-G2 {concept['concept_id']}: member outside its division or kind")
            membership.append(member)
    if sorted(membership) != sorted(released):
        fail("S8-G2 released functions and tasks are not partitioned exactly once into concepts")
    if len({c["concept_id"] for c in concepts["concepts"]}) != len(concepts["concepts"]):
        fail("S8-G2 concept identifier collision")
    ruled = {r["division_key"]: r for r in (rulings.get("rulings") or [])}
    reviewed_aliases = 0
    for division in concepts["divisions"]:
        key = division["division_key"]
        if division["review_status"] == "REVIEWED":
            ruling = ruled.get(key)
            if not ruling or not str(ruling.get("ruled_by", "")).strip() or not ruling.get("ruled_at") or not str(ruling.get("basis", "")).strip():
                fail(f"S8-G3 {key}: REVIEWED without a named, dated, argued ruling")
            reviewed_aliases += division["counts"]["aliases"]
        elif key in ruled or division["ruling"] is not None:
            fail(f"S8-G3 {key}: AUTO division carries a ruling")
    for concept in concepts["concepts"]:
        if concept["review_status"] == "AUTO" and (concept["basis"] != "machine_clustered" or concept["rationale"] is not None):
            fail(f"S8-G3 {concept['concept_id']}: AUTO concept claims an argued basis")
        if concept["review_status"] == "REVIEWED" and concept["division_key"] not in ruled:
            fail(f"S8-G3 {concept['concept_id']}: REVIEWED concept outside any ruling")
    if reviewed_aliases != concepts["counts"]["reviewed_aliases"]:
        fail("S8-G3 reviewed alias count does not reconcile")
    for problem in surface_problems(fixture, root=ROOT):
        fail(f"S8-G4 episode-surface fixture: {problem}")


def gate_public_eval_overlay() -> None:
    """S9-G1..G2 + S9-G5: overlay schema, paint rules, LLMAJ promote-gate."""
    from public_eval_overlay import OVERLAY_PATH, SCHEMA_PATH, overlay_problems
    from public_eval_llmaj import (
        FIXTURE_PATH,
        LEDGER_PATH,
        PREREG_PATH,
        cmd_promote_gate,
        ledger_problems,
        prereg_problems,
        schema_validate,
    )

    try:
        overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(f"S9-G1 public-eval overlay artifacts unreadable: {exc}")
        return
    try:
        import jsonschema

        jsonschema.Draft202012Validator.check_schema(schema)
        for error in jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).iter_errors(overlay):
            fail(f"S9-G1 overlay schema: {error.message[:120]}")
    except ImportError:
        pass
    for problem in overlay_problems(overlay, root=ROOT):
        fail(f"S9-G2 {problem}")

    # S9-G5: front-loaded prereg + LLMAJ promote-gate (no owner-steered saturation).
    try:
        for problem in prereg_problems():
            fail(f"S9-G5 prereg: {problem}")
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for msg in schema_validate(fixture):
            fail(f"S9-G5 fixture schema: {msg[:120]}")
        for problem in ledger_problems(fixture, allow_fixture_models=True):
            if "live ledger cannot use fixture" in problem:
                continue
            fail(f"S9-G5 fixture: {problem}")
        if LEDGER_PATH.is_file():
            ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
            for msg in schema_validate(ledger):
                fail(f"S9-G5 ledger schema: {msg[:120]}")
            for problem in ledger_problems(ledger, allow_fixture_models=False):
                fail(f"S9-G5 ledger: {problem}")
        if not PREREG_PATH.is_file():
            fail("S9-G5 missing public-eval LLMAJ prereg pack")
    except (OSError, ValueError) as exc:
        fail(f"S9-G5 LLMAJ artifacts unreadable: {exc}")
        return

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cmd_promote_gate()
    if rc != 0:
        for line in buf.getvalue().splitlines():
            if line.startswith("FAIL"):
                fail(f"S9-G5 {line[5:].strip()}")
        if not any(line.startswith("FAIL") for line in buf.getvalue().splitlines()):
            fail("S9-G5 promote-gate failed")

    # Meridian-facing observatory: cleanroom pin + LLMAJ empty-intersection story.
    try:
        from public_eval_observatory import cmd_check as observatory_check

        obs_buf = io.StringIO()
        with redirect_stdout(obs_buf):
            obs_rc = observatory_check()
        if obs_rc != 0:
            for line in obs_buf.getvalue().splitlines():
                if line.startswith("FAIL"):
                    fail(f"S9-G6 observatory: {line[5:].strip()}")
            if not any(line.startswith("FAIL") for line in obs_buf.getvalue().splitlines()):
                fail("S9-G6 public-eval observatory check failed")
    except (OSError, ValueError, ImportError) as exc:
        fail(f"S9-G6 public-eval observatory unreadable: {exc}")


def main() -> int:
    gate_cells()
    gate_run_summary()
    deny_scanned = gate_deny()
    gate_conformance_doc()
    gate_common_semantics()
    gate_release_manifest()
    gate_insight_construction()
    gate_worked_sample_calendar()
    pinned_cell = gate_compliance_scenarios()
    gate_replayable_compliance_scenario()
    gate_scenario_run_ledger()
    gate_schema_fixtures()
    gate_task_concepts()
    gate_public_eval_overlay()
    if FAILURES:
        print("GATE FAILURES:")
        for f in FAILURES:
            print("  ", f)
        return 1
    cells = len(list((ROOT / "cells").glob("*.json")))
    scenarios = len(list((ROOT / "specs/fixtures").glob("compliance-scenario-*.json")))
    print(
        f"all SPEC-03/SPEC-04/SPEC-05/SPEC-07/SPEC-08/SPEC-09 gates pass "
        f"({cells} cells, {scenarios} scenario fixture(s) pinning cell {pinned_cell}, "
        f"deny scan covered {deny_scanned} files, "
        f"CONFORMANCE.md intact at {CONFORMANCE_ROW_BASELINE} rows)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
