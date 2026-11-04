"""S3-G5: control-point cells bind to division keys admitted by the released taxonomy run."""
import builtins
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "tools"))
import gate_conformance as gate  # noqa: E402

ROOT = Path(__file__).parents[2]


def _stage(tmp_path, cell):
    (tmp_path / "specs").mkdir()
    (tmp_path / "cells").mkdir()
    (tmp_path / "reference").mkdir()
    (tmp_path / "live-run-20990101").mkdir()
    (tmp_path / "live-run-20260826").mkdir()
    schema = ROOT / "specs/control-point-cell.schema.json"
    (tmp_path / "specs" / schema.name).write_bytes(schema.read_bytes())
    (tmp_path / "reference/taxonomy-source.json").write_text(json.dumps({"run_dir": "live-run-20990101"}))
    (tmp_path / "live-run-20990101/matrix.csv").write_text("division_key,model_support,tier\nadmitted_key,2,STRONG\n")
    (tmp_path / "live-run-20260826/matrix.csv").write_text(
        "division_key,model_support,tier\ncollateral_margin_management,4,STRONG\n"
    )
    (tmp_path / "cells" / f"{cell['cell_id']}.json").write_text(json.dumps(cell))


def _base_cell():
    return json.loads((ROOT / "cells/cp_csa_vm_call_timeline.json").read_text())


def _remapped_cell():
    cell = _base_cell()
    cell["division_key"] = "admitted_key"
    return cell


def _check_staged(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    gate.FAILURES.clear()
    gate.gate_cells()
    return list(gate.FAILURES)


def test_every_published_cell_names_an_admitted_key_of_the_released_run():
    gate.FAILURES.clear()
    gate.gate_cells()
    assert gate.FAILURES == []
    admitted, run_dir = gate._admitted_division_keys()
    source = json.loads((ROOT / "reference/taxonomy-source.json").read_text())
    assert run_dir == source["run_dir"]
    for path in (ROOT / "cells").glob("*.json"):
        cell = json.loads(path.read_text())
        if cell["status"] != "RETIRED":
            assert cell["division_key"] in admitted, path.name
        for hist in cell.get("division_key_history") or []:
            assert hist["division_key"] != cell["division_key"]
            historical, _ = gate._admitted_division_keys(hist["taxonomy_run"])
            assert (hist["division_key"] in historical) == (hist.get("admission_status", "ADMITTED") == "ADMITTED")


def test_gate_rejects_cell_bound_to_retired_key(tmp_path, monkeypatch):
    cell = _base_cell()
    cell["division_key"] = "collateral_margin_management"
    cell.pop("division_key_history", None)
    _stage(tmp_path, cell)
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    gate.FAILURES.clear()
    gate.gate_cells()
    assert any("S3-G5" in f and "not admitted" in f for f in gate.FAILURES)


def test_gate_accepts_remapped_cell_and_rejects_bad_history(tmp_path, monkeypatch):
    cell = _remapped_cell()
    cell["division_key_history"] = [{
        "division_key": "admitted_key",            # repeats current key: rejected
        "taxonomy_run": "live-run-20000101",       # unknown run: rejected
        "superseded_on": "2026-11-03",
        "note": "stale binding carried from an earlier run",
    }]
    _stage(tmp_path, cell)
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    gate.FAILURES.clear()
    gate.gate_cells()
    assert any("unknown taxonomy run" in f for f in gate.FAILURES)
    assert any("repeats the current division_key" in f for f in gate.FAILURES)
    assert not any("not admitted" in f for f in gate.FAILURES)


def test_valid_prior_binding_is_checked_against_its_own_matrix(tmp_path, monkeypatch):
    _stage(tmp_path, _remapped_cell())
    assert _check_staged(tmp_path, monkeypatch) == []


def test_existing_run_directory_does_not_validate_an_invented_history_key(tmp_path, monkeypatch):
    cell = _remapped_cell()
    cell["division_key_history"][0]["division_key"] = "never_existed_key"
    _stage(tmp_path, cell)
    failures = _check_staged(tmp_path, monkeypatch)
    assert any("history 0" in f and "not admitted in live-run-20260826" in f for f in failures)


def test_explicitly_unadmitted_history_preserves_an_erroneous_binding(tmp_path, monkeypatch):
    cell = _remapped_cell()
    history = cell["division_key_history"][0]
    history.update(
        division_key="never_admitted_key",
        admission_status="UNADMITTED",
        note="Correction: the original proposal used a key absent from the historical taxonomy.",
    )
    _stage(tmp_path, cell)
    assert _check_staged(tmp_path, monkeypatch) == []


def test_unadmitted_status_cannot_hide_a_real_historical_admission(tmp_path, monkeypatch):
    cell = _remapped_cell()
    cell["division_key_history"][0]["admission_status"] = "UNADMITTED"
    _stage(tmp_path, cell)
    assert any("claims UNADMITTED" in f for f in _check_staged(tmp_path, monkeypatch))


@pytest.mark.parametrize("history", [None, {}, [None], ["bad"], [[]], [{}]])
def test_malformed_history_fails_without_crashing(tmp_path, monkeypatch, history):
    cell = _remapped_cell()
    cell["division_key_history"] = history
    _stage(tmp_path, cell)
    assert any("S3-G1" in f and "schema" in f for f in _check_staged(tmp_path, monkeypatch))


@pytest.mark.parametrize("value", [None, [], False, "not an object"])
def test_cell_must_be_a_json_object(tmp_path, monkeypatch, value):
    cell = _remapped_cell()
    _stage(tmp_path, cell)
    (tmp_path / "cells" / f"{cell['cell_id']}.json").write_text(json.dumps(value))
    assert any("cell must be a JSON object" in f for f in _check_staged(tmp_path, monkeypatch))


@pytest.mark.parametrize("source", [None, [], "live-run-20990101", {}, {"run_dir": []}])
def test_taxonomy_source_must_identify_a_named_run(tmp_path, monkeypatch, source):
    _stage(tmp_path, _remapped_cell())
    (tmp_path / "reference/taxonomy-source.json").write_text(json.dumps(source))
    assert any("S3-G5 taxonomy source" in f for f in _check_staged(tmp_path, monkeypatch))


@pytest.mark.parametrize("run_dir", [
    "", ".", "..", "../outside", "/tmp/outside", "C:\\tmp\\outside",
    "live-run-20260826/../live-run-20990101", "live-run-20260826\x00",
])
@pytest.mark.parametrize("location", ["current", "history"])
def test_taxonomy_paths_must_be_safe_named_runs(tmp_path, monkeypatch, run_dir, location):
    cell = _remapped_cell()
    if location == "history":
        cell["division_key_history"][0]["taxonomy_run"] = run_dir
    _stage(tmp_path, cell)
    if location == "current":
        (tmp_path / "reference/taxonomy-source.json").write_text(json.dumps({"run_dir": run_dir}))
    assert _check_staged(tmp_path, monkeypatch)


@pytest.mark.parametrize("run_dir", ["live-run-20990101", "live-run-20260826"])
@pytest.mark.parametrize("matrix", [
    "", "division_key,model_support,tier\n", "other,model_support,tier\nkey,2,STRONG\n",
    "division_key,model_support,tier,division_key\nkey,2,STRONG,key\n",
    "division_key,model_support,tier\nkey,2\n",
    "division_key,model_support,tier\nkey,2,STRONG,extra\n",
    "division_key,model_support,tier\nkey,2,STRONG\nkey,2,STRONG\n",
    'division_key,model_support,tier\n"unterminated,2,STRONG\n',
])
def test_current_and_historical_matrices_must_be_well_formed(tmp_path, monkeypatch, run_dir, matrix):
    _stage(tmp_path, _remapped_cell())
    (tmp_path / run_dir / "matrix.csv").write_text(matrix)
    assert any("S3-G5" in f and "matrix.csv" in f for f in _check_staged(tmp_path, monkeypatch))


@pytest.mark.parametrize("run_dir", ["live-run-20990101", "live-run-20260826"])
def test_missing_current_or_historical_matrix_fails(tmp_path, monkeypatch, run_dir):
    _stage(tmp_path, _remapped_cell())
    (tmp_path / run_dir / "matrix.csv").unlink()
    assert any("missing matrix.csv" in f for f in _check_staged(tmp_path, monkeypatch))


@pytest.mark.parametrize("target", ["run", "matrix"])
def test_taxonomy_symlinks_cannot_escape_the_repository(tmp_path, monkeypatch, target):
    root = tmp_path / "repo"
    root.mkdir()
    _stage(root, _remapped_cell())
    outside = tmp_path / "outside"
    outside.mkdir()
    run = root / "live-run-20260826"
    shutil.copyfile(run / "matrix.csv", outside / "matrix.csv")
    if target == "run":
        shutil.rmtree(run)
        run.symlink_to(outside, target_is_directory=True)
    else:
        (run / "matrix.csv").unlink()
        (run / "matrix.csv").symlink_to(outside / "matrix.csv")
    assert any("resolves outside" in f for f in _check_staged(root, monkeypatch))


def test_cell_schema_validation_cannot_be_silently_skipped(tmp_path, monkeypatch):
    _stage(tmp_path, _remapped_cell())
    original_import = builtins.__import__

    def without_jsonschema(name, *args, **kwargs):
        if name == "jsonschema":
            raise ImportError("synthetic unavailable dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_jsonschema)
    assert _check_staged(tmp_path, monkeypatch) == [
        "S3-G1 jsonschema is required to validate control-point cells"
    ]
