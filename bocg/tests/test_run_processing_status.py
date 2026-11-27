import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
RUN = ROOT / "live-run-20261110"


def test_november_run_records_its_approved_processing():
    status = json.loads((RUN / "processing-status.json").read_text())

    assert status["schema"] == "bocg.processing-status/v1"
    assert status["status"] == "PROCESSED"
    assert status["decision"] == "PROCESSED_WITH_OWNER_APPROVAL"
    assert status["inputs_rewritten"] is True
    assert status["taxonomy_source_updated"] is False
    assert status["taxonomy_source_run_dir"] == "live-run-20261019"
    assert status["eligibility"]["eligible_vendors"] == 2
    assert status["eligibility"]["g10"] == "FAIL"
    assert status["aliases"]["reviewed"] is False
    taxonomy_source = json.loads((ROOT / "reference/taxonomy-source.json").read_text())
    assert taxonomy_source["run_dir"] == status["taxonomy_source_run_dir"]

    report = json.loads((RUN / "gates_report.json").read_text())
    executed = {gate["id"]: gate["status"] for gate in report["gates"]}
    assert status["gates"] == executed
    assert status["gates_executed_at"] == report["ts_utc"]
    assert executed["G6"] == "FAIL"
    assert executed["G10"] == "FAIL"

    exclusions = json.loads((RUN / "exclusions.json").read_text())
    assert exclusions["consensus_policy"] == "eligible-models/v1"
    assert all(row["reason"] for row in exclusions["excluded"])

    expected_outputs = {
        "exclusions.json",
        "normalised.json",
        "canon_names.json",
        "matrix.csv",
        "matrix.json",
        "corroboration.csv",
        "corroboration_summary.json",
        "grid.json",
        "gates_report.json",
    }
    assert set(status["outputs_sha256"]) == expected_outputs
    for name, digest in status["outputs_sha256"].items():
        assert hashlib.sha256((RUN / name).read_bytes()).hexdigest() == digest, name
