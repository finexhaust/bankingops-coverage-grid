#!/usr/bin/env python3
"""Public-eval surface overlay: validate and roll up division saturation/voids.

Likelihood-matched projection of *public* rubrics/benchmarks/evals onto the
SPEC-08 episode-surface depth ladder. Painted rows
(QUALIFIED_MAPPING / RATIFIED_MAPPING on channel=public, paint-eligible inventory
class) drive saturation; admitted divisions with zero painted rows are voids.

BOCG control-point cells and their citations are not public evals and must not
paint. Own rubrics/evals use channel=own_artifact or own_cell and never paint.

    python3 tools/public_eval_overlay.py check
    python3 tools/public_eval_overlay.py build
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

from release_snapshots import load_release_artifact

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "reference/public-eval-inventory.v1.yaml"
OVERLAY_PATH = ROOT / "reference/public-eval-surface-map.v1.json"
SCHEMA_PATH = ROOT / "specs/public-eval-surface-overlay.schema.json"
PAINT = frozenset({"QUALIFIED_MAPPING", "RATIFIED_MAPPING"})
PAINT_CLASSES = frozenset(
    {"peer_framework", "peer_task_shape", "public_benchmark", "public_rubric"}
)
ID_FIELD_FOR_DEPTH = {
    "function_concept": "function_concept_id",
    "task_concept": "task_concept_id",
    "terminal_task": "task_reference_id",
    "control_point": "control_point_id",
}
BAND_WEIGHTS = {"L1": 1, "L2": 2, "L3": 3}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_inventory(*, root: Path = ROOT) -> dict:
    return yaml.safe_load((root / "reference/public-eval-inventory.v1.yaml").read_text(encoding="utf-8"))


def inventory_digest(*, root: Path = ROOT) -> str:
    return sha256_file(root / "reference/public-eval-inventory.v1.yaml")


def inventory_by_id(inventory: dict) -> dict[str, dict]:
    return {item["id"]: item for item in inventory.get("artifacts") or []}


def _canonical_digest(document: dict, digest_field: str) -> str:
    body = {key: value for key, value in document.items() if key != digest_field}
    return sha256_bytes(
        json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    )


def _released_surface(overlay: dict, *, root: Path) -> tuple[dict, dict, dict, str]:
    """Resolve the declared release; the overlay never supplies its own denominator."""
    binding = overlay.get("bocg_release") or {}
    if not isinstance(binding, dict):
        raise ValueError("bocg_release must be an object")
    tag = binding.get("tag")
    if not isinstance(tag, str) or not tag:
        raise ValueError("bocg_release.tag is required")

    def artifact(path: str) -> bytes:
        return load_release_artifact(root, path, release_tag=tag)

    concepts = json.loads(artifact("reference/task-concepts.v1.json"))
    catalogue_bytes = artifact("reference/operating-catalogue.v1.json")
    catalogue = json.loads(catalogue_bytes)
    for document, field in (
        (concepts, "task_concepts_sha256"),
        (catalogue, "catalogue_sha256"),
    ):
        if not isinstance(document, dict) or document.get(field) != _canonical_digest(document, field):
            raise ValueError(f"released {field} is invalid")
    if binding.get("task_concepts_sha256") != concepts["task_concepts_sha256"]:
        raise ValueError("bocg_release.task_concepts_sha256 does not match the pinned release")
    catalogue_digest = sha256_bytes(catalogue_bytes)
    concept_sources = {source["path"]: source["sha256"] for source in concepts["sources"]}
    if concept_sources.get("reference/operating-catalogue.v1.json") != catalogue_digest:
        raise ValueError("released task concepts name a different operating catalogue")

    matrix_sources = [source for source in catalogue["sources"] if source["path"].endswith("/matrix.json")]
    if len(matrix_sources) != 1:
        raise ValueError("released catalogue must bind exactly one taxonomy matrix")
    matrix_source = matrix_sources[0]
    matrix_bytes = artifact(matrix_source["path"])
    if sha256_bytes(matrix_bytes) != matrix_source["sha256"]:
        raise ValueError("released catalogue names a different taxonomy matrix")
    matrix = json.loads(matrix_bytes)
    divisions = admitted_divisions(catalogue)
    matrix_rows = matrix["rows"]
    reviews = concepts["divisions"]
    if (
        len(divisions) != len(set(divisions))
        or sorted(matrix["division_keys"]) != divisions
        or sorted(row["division_key"] for row in matrix_rows) != divisions
        or sorted(row["division_key"] for row in reviews) != divisions
    ):
        raise ValueError("released catalogue, task concepts and matrix disagree on admitted divisions")
    for records, key in ((concepts["concepts"], "concept_id"), (catalogue["definitions"], "reference_id")):
        if len({record[key] for record in records}) != len(records):
            raise ValueError(f"duplicate released {key}")
    return concepts, catalogue, matrix, catalogue_digest


def review_status_by_division(concepts: dict) -> dict[str, str]:
    return {d["division_key"]: d["review_status"] for d in concepts["divisions"]}


def admitted_divisions(catalogue: dict) -> list[str]:
    return sorted(
        d["division_key"]
        for d in catalogue["definitions"]
        if d["kind"] == "division"
    )


def paint_weight(row: dict, weights: dict[str, int], inv_item: dict | None) -> int:
    if row.get("mapping_status") not in PAINT:
        return 0
    if row.get("channel") != "public":
        return 0
    if not inv_item or inv_item.get("class") not in PAINT_CLASSES:
        return 0
    if row.get("depth") == "control_point" or row.get("control_point_id") is not None:
        return 0
    band = row.get("band")
    if band not in weights:
        return 0
    return int(weights[band])


def _division_rollup(overlay: dict, concepts: dict, catalogue: dict, matrix: dict, inventory: dict) -> dict:
    by_inv = inventory_by_id(inventory)
    tiers = {row["division_key"]: row["tier"] for row in matrix["rows"]}
    reviews = review_status_by_division(concepts)
    weights = dict(overlay["method"]["band_weights"])
    by_div: dict[str, list[dict]] = {key: [] for key in admitted_divisions(catalogue)}
    for row in overlay.get("rows") or []:
        inv_item = by_inv.get(row.get("inventory_id") or "")
        if paint_weight(row, weights, inv_item) <= 0:
            continue
        key = row.get("division_key")
        if key not in by_div:
            raise ValueError(f"painted division {key!r} is absent from the pinned catalogue")
        by_div[key].append(row)
    divisions = []
    max_sat = 0
    painted_divs = 0
    painted_rows = 0
    for key in sorted(by_div):
        rows = by_div[key]
        sat = sum(paint_weight(r, weights, by_inv.get(r["inventory_id"])) for r in rows)
        max_sat = max(max_sat, sat)
        if rows:
            painted_divs += 1
            painted_rows += len(rows)
        divisions.append(
            {
                "division_key": key,
                "review_status": reviews[key],
                "matrix_tier": tiers[key],
                "painted_rows": len(rows),
                "saturation": sat,
                "void": len(rows) == 0,
                "row_ids": [r["row_id"] for r in rows],
            }
        )
    return {
        "grain": "division",
        "band_weights": weights,
        "divisions": divisions,
        "summary": {
            "admitted_divisions": len(divisions),
            "painted_divisions": painted_divs,
            "void_divisions": len(divisions) - painted_divs,
            "painted_rows": painted_rows,
            "max_saturation": max_sat,
        },
    }


def compute_division_rollup(overlay: dict, *, root: Path = ROOT) -> dict:
    concepts, catalogue, matrix, _ = _released_surface(overlay, root=root)
    return _division_rollup(overlay, concepts, catalogue, matrix, load_inventory(root=root))


def compute_historical_division_rollup(overlay: dict, *, root: Path = ROOT) -> dict:
    """Historical and current overlays obey the same immutable release binding."""
    return compute_division_rollup(overlay, root=root)


def overlay_problems(overlay: dict, *, root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    try:
        concepts, catalogue, matrix, catalogue_digest = _released_surface(overlay, root=root)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        return [f"overlay release binding cannot be verified: {exc}"]
    prereg = json.loads((root / "reference/public-eval-llmaj-prereg.v1.json").read_text(encoding="utf-8"))
    inventory = load_inventory(root=root)
    by_inv = inventory_by_id(inventory)
    concept_ids = {c["concept_id"]: c for c in concepts["concepts"]}
    definitions = {d["reference_id"]: d for d in catalogue["definitions"]}
    divisions = {d["division_key"] for d in catalogue["definitions"] if d["kind"] == "division"}

    if overlay.get("bocg_release", {}).get("task_concepts_sha256") != prereg.get("inputs", {}).get("task_concepts_sha256"):
        problems.append("overlay is bound to a different task-concepts digest than the prereg")
    if catalogue_digest != prereg.get("inputs", {}).get("catalogue_sha256"):
        problems.append("overlay is bound to a different operating catalogue than the prereg")
    if overlay.get("inventory_sha256") != inventory_digest(root=root):
        problems.append("overlay inventory_sha256 does not match reference/public-eval-inventory.v1.yaml")

    method = overlay.get("method") or {}
    if set(method.get("paint_statuses") or []) != PAINT:
        problems.append("method.paint_statuses must be exactly QUALIFIED_MAPPING and RATIFIED_MAPPING")
    if method.get("band_weights") != BAND_WEIGHTS:
        problems.append("method.band_weights must be L1=1, L2=2, L3=3 for this release")
    if set(method.get("channels_in_saturation") or []) != {"public"}:
        problems.append("method.channels_in_saturation must be exactly ['public']")
    if set(method.get("paint_inventory_classes") or []) != PAINT_CLASSES:
        problems.append("method.paint_inventory_classes must be the public-eval class set only")
    if not method.get("llmaj_prereg_sha256"):
        problems.append("method.llmaj_prereg_sha256 is required (front-loaded LLMAJ prereg)")
    else:
        from public_eval_llmaj import overlay_non_influence_problems

        problems.extend(overlay_non_influence_problems(overlay))

    seen_rows: set[str] = set()
    for index, row in enumerate(overlay.get("rows") or []):
        where = f"row {index} ({row.get('row_id')})"
        rid = row.get("row_id")
        if rid in seen_rows:
            problems.append(f"{where}: duplicate row_id")
        seen_rows.add(rid)
        inv_id = row.get("inventory_id")
        inv_item = by_inv.get(inv_id or "")
        if inv_item is None:
            problems.append(f"{where}: unknown inventory_id")
        status = row.get("mapping_status")
        division = row.get("division_key")
        depth = row.get("depth")
        channel = row.get("channel")
        if status in PAINT:
            if channel != "public":
                problems.append(f"{where}: painted row must use channel=public")
            if inv_item and inv_item.get("class") not in PAINT_CLASSES:
                problems.append(
                    f"{where}: inventory class {inv_item.get('class')!r} cannot paint "
                    "(not a public rubric/benchmark/eval)"
                )
            if inv_item and inv_item.get("class") in {"own_rubric", "own_eval", "control_point_citation"}:
                problems.append(f"{where}: BOCG-own or citation inventory cannot paint public-eval saturation")
            if division not in divisions:
                problems.append(f"{where}: painted row needs an admitted division_key")
            if depth not in ID_FIELD_FOR_DEPTH and depth != "division":
                problems.append(f"{where}: painted row needs a SPEC-08 depth")
            if row.get("band") not in BAND_WEIGHTS:
                problems.append(f"{where}: painted row needs band L1|L2|L3")
            if not row.get("ruling"):
                problems.append(f"{where}: painted row needs a ruling")
            if not (row.get("rationale") or "").strip():
                problems.append(f"{where}: painted row needs a rationale")
            if depth == "control_point" or row.get("control_point_id") is not None:
                problems.append(
                    f"{where}: control_point depth must not paint public-eval saturation "
                    "(BOCG cell coverage is not a public eval)"
                )
        elif division is not None and division not in divisions:
            if status not in {"DEFERRED_MAPPING", "REJECTED_MAPPING"}:
                problems.append(f"{where}: unknown division {division!r}")
        field = ID_FIELD_FOR_DEPTH.get(depth) if depth else None
        if field and not row.get(field):
            problems.append(f"{where}: depth {depth} needs {field}")
        for key, kind in (("function_concept_id", "function_concept"), ("task_concept_id", "task_concept")):
            value = row.get(key)
            if value is None:
                continue
            concept = concept_ids.get(value)
            if concept is None:
                problems.append(f"{where}: {key} is not a released concept")
            elif concept["kind"] != kind or concept["division_key"] != division:
                problems.append(f"{where}: {key} belongs to another kind or division")
        task_ref = row.get("task_reference_id")
        if task_ref is not None:
            definition = definitions.get(task_ref)
            if definition is None or definition["kind"] != "task" or definition["division_key"] != division:
                problems.append(f"{where}: task_reference_id is not a released task of the division")
            elif row.get("task_concept_id") in concept_ids:
                if task_ref not in concept_ids[row["task_concept_id"]]["members"]:
                    problems.append(f"{where}: task_reference_id is not a member of task_concept_id")
        cell = row.get("control_point_id")
        if cell is not None:
            try:
                released_cell = json.loads(load_release_artifact(
                    root, f"cells/{cell}.json", release_tag=overlay["bocg_release"]["tag"]
                ))
                if not isinstance(released_cell, dict) or released_cell.get("cell_id") != cell:
                    raise ValueError("cell identifier differs from its released artifact")
            except (KeyError, TypeError, ValueError, OSError) as exc:
                problems.append(f"{where}: control_point_id is not a released cell: {exc}")
            else:
                cell_division = released_cell.get("division_key")
                if cell_division not in divisions or cell_division != division:
                    problems.append(f"{where}: control_point_id belongs to another or unadmitted division")

    try:
        expected = _division_rollup(overlay, concepts, catalogue, matrix, inventory)
    except (KeyError, TypeError, ValueError) as exc:
        problems.append(f"division_rollup cannot be verified against its pinned division set: {exc}")
        return problems
    if overlay.get("division_rollup") != expected:
        problems.append("division_rollup does not match the pinned catalogue / painted public-eval rows / band weights")
    return problems


def refresh_rollup_and_digest(overlay: dict, *, root: Path = ROOT) -> dict:
    overlay = dict(overlay)
    overlay["inventory_sha256"] = inventory_digest(root=root)
    overlay["division_rollup"] = compute_division_rollup(overlay, root=root)
    return overlay


def cmd_build() -> int:
    overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))
    method = dict(overlay.get("method") or {})
    method.setdefault(
        "paint_inventory_classes",
        sorted(PAINT_CLASSES),
    )
    overlay["method"] = method
    overlay = refresh_rollup_and_digest(overlay)
    OVERLAY_PATH.write_text(json.dumps(overlay, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OVERLAY_PATH.relative_to(ROOT)}")
    print("summary:", overlay["division_rollup"]["summary"])
    return 0


def cmd_check() -> int:
    overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))
    try:
        import jsonschema

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        errors = sorted(
            jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).iter_errors(overlay),
            key=lambda e: list(e.path),
        )
        for err in errors:
            print("FAIL schema:", err.message)
        schema_failed = bool(errors)
    except ImportError:
        print("FAIL jsonschema not installed; schema validation is required")
        return 1
    problems = overlay_problems(overlay)
    for problem in problems:
        print("FAIL", problem)
    # S9-G5: public_benchmark paint is LLMAJ multi-pass only (never one-pass owner).
    from public_eval_llmaj import cmd_promote_gate

    promote_rc = cmd_promote_gate()
    if schema_failed or problems or promote_rc != 0:
        return 1
    summary = overlay["division_rollup"]["summary"]
    print(
        f"ok painted={summary['painted_divisions']} voids={summary['void_divisions']} "
        f"rows={summary['painted_rows']} max_sat={summary['max_saturation']}"
    )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build"))
    args = parser.parse_args(argv)
    if args.command == "check":
        return cmd_check()
    return cmd_build()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
