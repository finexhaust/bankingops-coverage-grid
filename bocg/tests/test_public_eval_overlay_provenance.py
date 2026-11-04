"""Historical public-eval mappings must remain bound to their released surface."""
import builtins
import copy
import json
import shutil
from pathlib import Path

import pytest

import public_eval_overlay as overlay_tools
from release_snapshots import load_release_artifact

ROOT = Path(__file__).parents[2]


@pytest.fixture
def overlay():
    return json.loads((ROOT / "reference/public-eval-surface-map.v1.json").read_text())


def _painted(overlay):
    return next(row for row in overlay["rows"] if row["mapping_status"] in overlay_tools.PAINT)


def _released(overlay, path):
    return json.loads(load_release_artifact(ROOT, path, release_tag=overlay["bocg_release"]["tag"]))


def _issues(overlay, *, root=ROOT):
    return overlay_tools.overlay_problems(overlay, root=root)


def _copy_validation_inputs(tmp_path):
    for path in (
        "reference/public-eval-llmaj-prereg.v1.json",
        "reference/public-eval-inventory.v1.yaml",
        "specs/bocg-release-manifest.schema.json",
    ):
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, destination)
    shutil.copytree(ROOT / "reference/release-snapshots", tmp_path / "reference/release-snapshots")


def test_historical_overlay_reproduces_against_its_release(overlay):
    current = json.loads((ROOT / "reference/task-concepts.v1.json").read_text())
    assert current["task_concepts_sha256"] != overlay["bocg_release"]["task_concepts_sha256"]
    assert _issues(overlay) == []
    expected = overlay_tools.compute_historical_division_rollup(overlay)
    assert expected == overlay["division_rollup"]
    assert expected["summary"] == {
        "admitted_divisions": 42,
        "painted_divisions": 1,
        "void_divisions": 41,
        "painted_rows": 1,
        "max_saturation": 1,
    }


@pytest.mark.parametrize("mutation", ["drop_void", "invent_division", "review_status", "matrix_tier"])
def test_historical_rollup_cannot_supply_its_own_denominator_or_labels(overlay, mutation):
    rollup = overlay["division_rollup"]
    void = next(row for row in rollup["divisions"] if row["void"])
    if mutation == "drop_void":
        rollup["divisions"].remove(void)
        rollup["summary"]["admitted_divisions"] -= 1
        rollup["summary"]["void_divisions"] -= 1
    elif mutation == "invent_division":
        void["division_key"] = "invented_division"
    elif mutation == "review_status":
        void["review_status"] = "REVIEWED" if void["review_status"] == "AUTO" else "AUTO"
    else:
        void["matrix_tier"] = "STRONG" if void["matrix_tier"] == "WEAK" else "WEAK"
    assert any("division_rollup does not match the pinned catalogue" in issue for issue in _issues(overlay))
    assert overlay_tools.compute_historical_division_rollup(overlay)["summary"]["admitted_divisions"] == 42


def test_unknown_release_tag_cannot_reuse_known_task_digest(overlay):
    overlay["bocg_release"]["tag"] = "v99.0.0"
    assert any("release binding cannot be verified" in issue for issue in _issues(overlay))
    with pytest.raises(ValueError, match="unknown or mismatched release pin"):
        overlay_tools.compute_historical_division_rollup(overlay)


def test_historical_task_digest_must_match_the_verified_release(overlay):
    overlay["bocg_release"]["task_concepts_sha256"] = "f" * 64
    assert any("task_concepts_sha256 does not match the pinned release" in issue for issue in _issues(overlay))


@pytest.mark.parametrize(
    "field,depth,identifier,message",
    [
        ("function_concept_id", "function_concept", "function_concept:trade_lifecycle_operations:" + "0" * 24, "not a released concept"),
        ("task_concept_id", "task_concept", "task_concept:trade_lifecycle_operations:" + "0" * 24, "not a released concept"),
        ("task_reference_id", "terminal_task", "task:trade_lifecycle_operations:" + "0" * 24, "not a released task"),
    ],
)
def test_historical_overlay_rejects_unknown_references(overlay, field, depth, identifier, message):
    row = _painted(overlay)
    row["depth"] = depth
    row[field] = identifier
    assert any(field in issue and message in issue for issue in _issues(overlay))


@pytest.mark.parametrize("mismatch", ["kind", "division"])
def test_historical_concepts_must_match_the_row_kind_and_division(overlay, mismatch):
    row = _painted(overlay)
    concepts = _released(overlay, "reference/task-concepts.v1.json")["concepts"]
    if mismatch == "kind":
        concept = next(c for c in concepts if c["kind"] == "task_concept" and c["division_key"] == row["division_key"])
    else:
        concept = next(c for c in concepts if c["kind"] == "function_concept" and c["division_key"] != row["division_key"])
    row["depth"] = "function_concept"
    row["function_concept_id"] = concept["concept_id"]
    assert any("function_concept_id belongs to another kind or division" in issue for issue in _issues(overlay))


@pytest.mark.parametrize("mismatch", ["kind", "division", "concept_membership"])
def test_historical_tasks_must_match_kind_division_and_concept(overlay, mismatch):
    row = _painted(overlay)
    definitions = _released(overlay, "reference/operating-catalogue.v1.json")["definitions"]
    if mismatch == "kind":
        definition = next(d for d in definitions if d["kind"] == "function" and d["division_key"] == row["division_key"])
    elif mismatch == "division":
        definition = next(d for d in definitions if d["kind"] == "task" and d["division_key"] != row["division_key"])
    else:
        concepts = _released(overlay, "reference/task-concepts.v1.json")["concepts"]
        concept = next(c for c in concepts if c["kind"] == "task_concept" and c["division_key"] == row["division_key"])
        row["task_concept_id"] = concept["concept_id"]
        definition = next(
            d for d in definitions if d["kind"] == "task" and d["division_key"] == row["division_key"]
            and d["reference_id"] not in concept["members"]
        )
    row["depth"] = "terminal_task"
    row["task_reference_id"] = definition["reference_id"]
    expected = "not a member of task_concept_id" if mismatch == "concept_membership" else "not a released task of the division"
    assert any(expected in issue for issue in _issues(overlay))


def test_historical_cell_validation_uses_the_released_binding(overlay):
    cell_id = "cp_csa_vm_call_timeline"
    released_cell = _released(overlay, f"cells/{cell_id}.json")
    current_cell = json.loads((ROOT / f"cells/{cell_id}.json").read_text())
    assert released_cell["division_key"] != current_cell["division_key"]
    row = copy.deepcopy(_painted(overlay))
    row.update(
        row_id="ovr_historical_cell_candidate",
        mapping_status="PENDING",
        channel="own_cell",
        depth="control_point",
        control_point_id=cell_id,
        division_key=released_cell["division_key"],
        band=None,
        ruling=None,
    )
    overlay["rows"].append(row)
    assert _issues(overlay) == []
    row["division_key"] = current_cell["division_key"]
    assert any("control_point_id belongs to another or unadmitted division" in issue for issue in _issues(overlay))


@pytest.mark.parametrize("depth,cell_id", [("control_point", "cp_csa_vm_call_timeline"), ("division", "cp_csa_vm_call_timeline"), ("control_point", None)])
def test_control_point_paint_is_rejected_even_for_historical_or_incomplete_rows(overlay, depth, cell_id):
    row = _painted(overlay)
    row.update(depth=depth, control_point_id=cell_id)
    if cell_id:
        row["division_key"] = _released(overlay, f"cells/{cell_id}.json")["division_key"]
    assert any("control_point depth must not paint" in issue for issue in _issues(overlay))
    assert overlay_tools.paint_weight(row, overlay_tools.BAND_WEIGHTS, {"class": "peer_task_shape"}) == 0


def test_unreleased_cell_is_rejected_in_historical_mode(overlay):
    row = copy.deepcopy(_painted(overlay))
    row.update(row_id="ovr_missing_cell", mapping_status="PENDING", channel="own_cell", depth="control_point", control_point_id="cp_unreleased")
    overlay["rows"].append(row)
    assert any("control_point_id is not a released cell" in issue for issue in _issues(overlay))


def test_historical_overlay_does_not_depend_on_mutable_current_catalogue(tmp_path, overlay):
    _copy_validation_inputs(tmp_path)
    # No current catalogue, task-concepts file or matrix exists in this workspace.
    assert _issues(overlay, root=tmp_path) == []
    assert overlay_tools.compute_historical_division_rollup(overlay, root=tmp_path) == overlay["division_rollup"]


def test_historical_snapshot_tampering_is_rejected_before_rollup(tmp_path, overlay):
    _copy_validation_inputs(tmp_path)
    path = tmp_path / "reference/release-snapshots/v0.6.2/reference/operating-catalogue.v1.json"
    catalogue = json.loads(path.read_text())
    catalogue["definitions"].pop()
    path.write_text(json.dumps(catalogue))
    assert any("pinned release artifact digest mismatch" in issue for issue in _issues(overlay, root=tmp_path))


def test_historical_catalogue_must_match_preregistered_input(tmp_path, overlay):
    _copy_validation_inputs(tmp_path)
    path = tmp_path / "reference/public-eval-llmaj-prereg.v1.json"
    prereg = json.loads(path.read_text())
    prereg["inputs"]["catalogue_sha256"] = "f" * 64
    path.write_text(json.dumps(prereg))
    assert "overlay is bound to a different operating catalogue than the prereg" in _issues(overlay, root=tmp_path)


def test_overlay_cli_fails_closed_without_jsonschema(monkeypatch, capsys):
    original_import = builtins.__import__

    def import_without_jsonschema(name, *args, **kwargs):
        if name == "jsonschema":
            raise ImportError("schema dependency unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_jsonschema)
    assert overlay_tools.cmd_check() == 1
    assert "schema validation is required" in capsys.readouterr().out
