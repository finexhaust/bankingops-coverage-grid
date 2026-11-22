import json
from pathlib import Path

import gate_conformance
from calendar_gate import validate_dated_sample
from build_release_manifest import STATIC_ARTIFACTS


ROOT = Path(__file__).parents[2]
CALENDARS = json.loads((ROOT / "reference/business-calendars.v1.json").read_text())


def _sample():
    return json.loads(
        (ROOT / "reference/worked-samples/fm-pb-0417-r3.json").read_text()
    )


def test_published_r3_dates_pass_calendar_validation():
    assert validate_dated_sample(_sample(), CALENDARS) == []


def test_withdrawn_r2_holiday_is_rejected_by_calendar_validation():
    sample = json.loads(
        (ROOT / "specs/fixtures/worked-sample-r2-withdrawn.json").read_text()
    )
    errors = validate_dated_sample(sample, CALENDARS)
    assert any("marks holiday 2026-05-25 open on FED" in error for error in errors)


def test_settlement_and_cutoff_events_require_a_known_calendar():
    sample = _sample()
    sample["dated_events"][0].pop("calendar_ref")
    sample["dated_events"][1]["calendar_ref"] = "UNKNOWN"
    errors = validate_dated_sample(sample, CALENDARS)
    assert any("dated event 0 has no calendar_ref" in error for error in errors)
    assert any("refers to unknown calendar 'UNKNOWN'" in error for error in errors)


def test_open_weekends_and_dates_outside_calendar_coverage_are_rejected():
    sample = _sample()
    sample["dated_events"][0]["date"] = "2026-05-23"
    sample["dated_events"][1]["date"] = "2027-01-04"
    errors = validate_dated_sample(sample, CALENDARS)
    assert any("marks weekend 2026-05-23 open on FED" in error for error in errors)
    assert any("outside 'FED' coverage" in error for error in errors)


def test_closed_holiday_is_permitted():
    sample = _sample()
    sample["dated_events"] = [
        {
            "date": "2026-05-25",
            "event_type": "settlement",
            "calendar_ref": "FED",
            "status": "closed",
        }
    ]
    assert validate_dated_sample(sample, CALENDARS) == []


def test_spec05_gate_accepts_the_published_r3(tmp_path, monkeypatch):
    (tmp_path / "reference/worked-samples").mkdir(parents=True)
    (tmp_path / "specs").mkdir()
    for relative in (
        "reference/business-calendars.v1.json",
        "reference/worked-samples/fm-pb-0417-r3.json",
        "specs/insight-construction-profile.yaml",
    ):
        (tmp_path / relative).write_bytes((ROOT / relative).read_bytes())
    monkeypatch.setattr(gate_conformance, "ROOT", tmp_path)
    previous_failures = list(gate_conformance.FAILURES)
    gate_conformance.FAILURES.clear()
    try:
        gate_conformance.gate_worked_sample_calendar()
        assert gate_conformance.FAILURES == []
    finally:
        gate_conformance.FAILURES[:] = previous_failures


def test_spec05_gate_rejects_an_invalid_published_sample(tmp_path, monkeypatch):
    (tmp_path / "reference/worked-samples").mkdir(parents=True)
    (tmp_path / "specs").mkdir()
    for relative in (
        "reference/business-calendars.v1.json",
        "reference/worked-samples/fm-pb-0417-r3.json",
        "specs/insight-construction-profile.yaml",
    ):
        (tmp_path / relative).write_bytes((ROOT / relative).read_bytes())
    sample_path = tmp_path / "reference/worked-samples/fm-pb-0417-r3.json"
    sample = json.loads(sample_path.read_text())
    sample["dated_events"][0]["date"] = "2026-05-25"
    sample_path.write_text(json.dumps(sample))
    monkeypatch.setattr(gate_conformance, "ROOT", tmp_path)
    previous_failures = list(gate_conformance.FAILURES)
    gate_conformance.FAILURES.clear()
    try:
        gate_conformance.gate_worked_sample_calendar()
        assert any("marks holiday 2026-05-25 open on FED" in error
                   for error in gate_conformance.FAILURES)
    finally:
        gate_conformance.FAILURES[:] = previous_failures


def test_calendar_and_published_sample_are_release_manifest_artifacts():
    assert STATIC_ARTIFACTS["reference/business-calendars.v1.json"] == "business-calendar-reference"
    assert STATIC_ARTIFACTS[
        "reference/worked-samples/fm-pb-0417-r3.json"
    ] == "dated-worked-sample"
