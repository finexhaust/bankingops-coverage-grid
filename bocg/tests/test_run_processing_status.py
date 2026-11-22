import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
RUN = ROOT / "live-run-20261110"


def test_november_run_records_why_it_is_unprocessed():
    status = json.loads((RUN / "processing-status.json").read_text())

    assert status["schema"] == "bocg.processing-status/v1"
    assert status["status"] == "UNPROCESSED"
    assert status["decision"] == "NOT_PROCESSED_PENDING_OWNER_APPROVAL"
    assert status["inputs_rewritten"] is False
    assert status["taxonomy_source_updated"] is False
    assert status["taxonomy_source_run_dir"] == "live-run-20261019"
    assert status["eligibility"]["eligible_vendors"] == 2
    assert status["eligibility"]["g10"] == "FAIL"
    assert status["aliases"]["reviewed"] is False
    taxonomy_source = json.loads((ROOT / "reference/taxonomy-source.json").read_text())
    assert taxonomy_source["run_dir"] == status["taxonomy_source_run_dir"]

    expected_outputs = {
        "exclusions.json",
        "matrix.csv",
        "matrix.json",
        "corroboration.csv",
        "corroboration_summary.json",
        "grid.json",
        "gates_report.json",
        "RUN_SUMMARY.json",
        "postprocessing-receipt.json",
    }
    assert set(status["outputs_not_created"]) == expected_outputs
    for name in expected_outputs:
        assert not (RUN / name).exists(), name
