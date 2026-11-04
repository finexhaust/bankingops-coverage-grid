"""S3-G5: control-point cells bind to division keys admitted by the released taxonomy run."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "tools"))
import gate_conformance as gate  # noqa: E402

ROOT = Path(__file__).parents[2]


def _stage(tmp_path, cell):
    (tmp_path / "specs").mkdir()
    (tmp_path / "cells").mkdir()
    (tmp_path / "reference").mkdir()
    (tmp_path / "live-run-20990101").mkdir()
    schema = ROOT / "specs/control-point-cell.schema.json"
    (tmp_path / "specs" / schema.name).write_bytes(schema.read_bytes())
    (tmp_path / "reference/taxonomy-source.json").write_text(json.dumps({"run_dir": "live-run-20990101"}))
    (tmp_path / "live-run-20990101/matrix.csv").write_text("division_key,model_support,tier\nadmitted_key,2,STRONG\n")
    (tmp_path / "cells" / f"{cell['cell_id']}.json").write_text(json.dumps(cell))


def _base_cell():
    return json.loads((ROOT / "cells/cp_csa_vm_call_timeline.json").read_text())


def test_every_published_cell_names_an_admitted_key_of_the_released_run():
    gate.FAILURES.clear()
    gate.gate_cells()
    assert [f for f in gate.FAILURES if f.startswith("S3-G5")] == []
    admitted, run_dir = gate._admitted_division_keys()
    source = json.loads((ROOT / "reference/taxonomy-source.json").read_text())
    assert run_dir == source["run_dir"]
    for path in (ROOT / "cells").glob("*.json"):
        cell = json.loads(path.read_text())
        if cell["status"] != "RETIRED":
            assert cell["division_key"] in admitted, path.name
        for hist in cell.get("division_key_history") or []:
            assert hist["division_key"] != cell["division_key"]
            assert (ROOT / hist["taxonomy_run"]).is_dir()


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
    cell = _base_cell()
    cell["division_key"] = "admitted_key"
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
