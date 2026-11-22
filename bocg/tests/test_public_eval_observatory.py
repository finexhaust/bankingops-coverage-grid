"""The public observatory must surface its pinned companion release audit."""
import copy

import pytest

import public_eval_observatory as observatory


@pytest.fixture
def doc():
    return observatory.build_observatory()


def test_observatory_projects_companion_archive_and_audit_evidence(doc):
    cleanroom = doc["cleanroom_eval"]
    assert cleanroom["release_archive_sha256"] == (
        "02184bb6fb3227f890488e16865aa6d994b0025583f613093d67363651a427d5"
    )
    assert cleanroom["release_audit_sha256"] == (
        "234db03f6b4516706e762ade9ef2bd6b04c10d79ca6aa2130e96d897e77b31bc"
    )
    assert cleanroom["release_audit_terminal_state"] == "RELEASE_AUDIT_PASS_WITH_LIMITATIONS"
    assert cleanroom["release_audit_gate_counts"] == {
        "total": 13,
        "passed": 10,
        "failed": 0,
        "not_run": 3,
    }


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("release_archive_sha256", "f" * 64),
        ("release_audit_sha256", "e" * 64),
        ("release_audit_terminal_state", "RELEASE_AUDIT_PASS"),
        ("release_audit_gate_counts", {"total": 13, "passed": 13, "failed": 0, "not_run": 0}),
    ],
)
def test_observatory_rejects_companion_audit_evidence_drift(doc, field, changed):
    doc = copy.deepcopy(doc)
    doc["cleanroom_eval"][field] = changed
    assert f"cleanroom_eval.{field} drifted from companion pin" in observatory.observatory_problems(doc)
