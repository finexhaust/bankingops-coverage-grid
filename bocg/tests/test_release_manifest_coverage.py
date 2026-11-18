"""The release manifest pins every recorded run and the worked sample."""
import hashlib
import subprocess
from pathlib import Path

from build_release_manifest import EVIDENCE_SUFFIXES, build_manifest

ROOT = Path(__file__).parents[2]


def _manifest():
    return build_manifest(
        tag="v0.0.0-test", commit_sha="a" * 40, generated_at="2026-11-18T00:00:00Z", root=ROOT
    )


def _tracked(pattern):
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", pattern], cwd=ROOT, check=True, capture_output=True
    ).stdout.decode()
    return [p for p in out.split("\0") if p]


def test_every_tracked_run_evidence_file_is_pinned():
    rows = {row["path"]: row for row in _manifest()["artifacts"]}
    expected = [
        p for p in _tracked("live-run-*")
        if Path(p).suffix in EVIDENCE_SUFFIXES and (ROOT / p).stat().st_size > 0
    ]
    assert expected, "no live-run evidence found"
    missing = [p for p in expected if p not in rows]
    assert missing == []
    for path in expected:
        assert rows[path]["sha256"] == hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_every_live_run_directory_is_represented():
    paths = {row["path"] for row in _manifest()["artifacts"]}
    runs = sorted(p.name for p in ROOT.glob("live-run-*") if p.is_dir())
    assert runs
    for run in runs:
        assert any(path.startswith(run + "/") for path in paths), run


def test_worked_sample_is_pinned_as_documentation():
    rows = {row["path"]: row for row in _manifest()["artifacts"]}
    row = rows["WORKED-SAMPLE.md"]
    assert row["role"] == "documentation"
    assert row["sha256"] == hashlib.sha256((ROOT / "WORKED-SAMPLE.md").read_bytes()).hexdigest()


def test_existing_roles_are_not_overridden_by_the_run_sweep():
    rows = {row["path"]: row for row in _manifest()["artifacts"]}
    # The current run's named artifacts keep their specific roles.
    assert any(row["role"] == "coverage-matrix" for row in rows.values())
    # Verified historical snapshot evidence keeps its role.
    assert any(row["role"] == "historical-release-evidence" for row in rows.values())
