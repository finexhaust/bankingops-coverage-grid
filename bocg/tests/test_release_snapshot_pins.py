"""Historical pins must verify offline, including in a checkout without .git."""
import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import gate_conformance as gate  # noqa: E402
from build_release_manifest import canonical_json, sha256_bytes  # noqa: E402
from release_snapshots import (  # noqa: E402
    ReleaseSnapshotError, load_release_artifact, load_release_manifest, validate_manifest,
    verified_archive_paths,
)


@pytest.fixture
def checkout(tmp_path):
    shutil.copytree(ROOT / "reference/release-snapshots", tmp_path / "reference/release-snapshots")
    (tmp_path / "specs/fixtures").mkdir(parents=True)
    for relative in (
        "specs/bocg-release-manifest.schema.json",
        "specs/compliance-scenario.schema.json",
        "specs/fixtures/compliance-scenario-synthetic.json",
    ):
        shutil.copyfile(ROOT / relative, tmp_path / relative)
    return tmp_path


def _scenario(checkout, monkeypatch, **changes):
    fixture = checkout / "specs/fixtures/compliance-scenario-synthetic.json"
    obj = json.loads(fixture.read_text())
    obj.update(changes)
    fixture.write_text(json.dumps(obj))
    monkeypatch.setattr(gate, "ROOT", checkout)
    gate.FAILURES.clear()
    gate.gate_compliance_scenarios()
    return list(gate.FAILURES)


def test_known_historical_scenario_verifies_without_git_or_embedded_manifest(checkout, monkeypatch):
    assert not (checkout / ".git").exists()
    assert not (checkout / "bocg-release-manifest.json").exists()
    assert _scenario(checkout, monkeypatch) == []


@pytest.mark.parametrize("pin", ["f" * 64, "0" * 64, None])
def test_unknown_or_empty_scenario_pin_never_disables_validation(checkout, monkeypatch, pin):
    assert _scenario(checkout, monkeypatch, manifest_sha256=pin)


@pytest.mark.parametrize("payload", [None, [], {}, "not a manifest"])
def test_present_malformed_manifest_is_not_treated_as_absent(checkout, monkeypatch, payload):
    (checkout / "bocg-release-manifest.json").write_text(json.dumps(payload))
    failures = _scenario(checkout, monkeypatch)
    assert any("S7-G5 local release manifest is invalid" in f for f in failures)


def test_unknown_scenario_references_cannot_use_current_checkout_files(checkout, monkeypatch):
    (checkout / "cells").mkdir()
    (checkout / "cells/cp_unreleased.json").write_text('{"cell_id":"cp_unreleased"}')
    failures = _scenario(checkout, monkeypatch, cell_id="cp_unreleased")
    assert any("not in the pinned release" in f for f in failures)
    failures = _scenario(checkout, monkeypatch, cell_id="cp_settled_instruction_amendment",
                         task_ref="task:buyside_trading_execution:000000000000000000000000")
    assert any("task_ref is not a task" in f for f in failures)


def test_snapshot_artifact_tamper_is_rejected(checkout, monkeypatch):
    path = checkout / "reference/release-snapshots/v0.6.3/cells/cp_settled_instruction_amendment.json"
    path.write_bytes(path.read_bytes() + b" ")
    assert any("digest mismatch" in f for f in _scenario(checkout, monkeypatch))


def test_snapshot_manifest_tamper_is_rejected(checkout):
    path = checkout / "reference/release-snapshots/v0.6.2/bocg-release-manifest.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ReleaseSnapshotError, match="manifest file digest mismatch"):
        load_release_manifest(checkout, release_tag="v0.6.2")


def test_unknown_tag_and_cross_release_pin_are_rejected(checkout):
    with pytest.raises(ReleaseSnapshotError, match="unknown or mismatched"):
        load_release_manifest(checkout, release_tag="v99.0.0")
    prior = load_release_manifest(checkout, release_tag="v0.6.2")
    with pytest.raises(ReleaseSnapshotError, match="unknown or mismatched"):
        load_release_manifest(checkout, release_tag="v0.6.3", manifest_sha256=prior["manifest_sha256"])


def test_manifest_self_digest_and_aggregate_are_both_enforced(checkout):
    original = load_release_manifest(checkout, release_tag="v0.6.3")
    changed = copy.deepcopy(original)
    changed["release"]["generated_at"] = "2026-01-01T00:00:00Z"
    with pytest.raises(ReleaseSnapshotError, match="self digest mismatch"):
        validate_manifest(changed, root=checkout)
    changed = copy.deepcopy(original)
    changed["artifacts"][0]["sha256"] = "e" * 64
    changed["manifest_sha256"] = sha256_bytes(canonical_json(
        {k: v for k, v in changed.items() if k != "manifest_sha256"}
    ))
    with pytest.raises(ReleaseSnapshotError, match="aggregate digest mismatch"):
        validate_manifest(changed, root=checkout)


@pytest.mark.parametrize("include_tag", [False, True])
def test_local_manifest_cannot_shadow_an_indexed_release(checkout, include_tag):
    manifest = load_release_manifest(checkout, release_tag="v0.6.2")
    manifest["release"]["generated_at"] = "2026-01-01T00:00:00Z"
    manifest["manifest_sha256"] = sha256_bytes(canonical_json(
        {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    ))
    (checkout / "bocg-release-manifest.json").write_text(json.dumps(manifest))
    args = {"manifest_sha256": manifest["manifest_sha256"]}
    if include_tag:
        args["release_tag"] = "v0.6.2"
    with pytest.raises(ReleaseSnapshotError, match="mismatched|conflicts"):
        load_release_manifest(checkout, **args)


def test_duplicate_paths_cannot_make_artifact_selection_ambiguous(checkout):
    manifest = load_release_manifest(checkout, release_tag="v0.6.3")
    manifest["artifacts"].append(copy.deepcopy(manifest["artifacts"][0]))
    with pytest.raises(ReleaseSnapshotError, match="duplicate artifact"):
        validate_manifest(manifest, root=checkout)


def test_packaging_cannot_omit_the_historical_catalogue(checkout):
    path = checkout / "reference/release-snapshots/index.json"
    index = json.loads(path.read_text())
    index["releases"][0]["retained_artifacts"].remove("reference/operating-catalogue.v1.json")
    path.write_text(json.dumps(index))
    with pytest.raises(ReleaseSnapshotError, match="omits required"):
        verified_archive_paths(checkout)


def test_scenario_timestamp_format_is_enforced(checkout, monkeypatch):
    failures = _scenario(checkout, monkeypatch, deadline={
        "regime_clock_ref": "synthetic deadline", "observed_at": "not-a-timestamp",
    })
    assert any("S7-G1 fixture schema" in f for f in failures)


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_scenario_numbers_are_invalid_json(checkout, monkeypatch, threshold):
    fixture = json.loads((checkout / "specs/fixtures/compliance-scenario-synthetic.json").read_text())
    fixture["pass_rule"]["statistical_assertion"]["threshold"] = threshold
    assert any("nonfinite JSON" in f for f in _scenario(checkout, monkeypatch, **fixture))


@pytest.mark.parametrize("path", ["../outside.json", "/tmp/outside.json", "cells/../outside.json", "cells\\outside.json"])
def test_artifact_paths_cannot_escape_snapshot(checkout, path):
    with pytest.raises(ReleaseSnapshotError, match="unsafe release artifact path"):
        load_release_artifact(checkout, path, release_tag="v0.6.2")


def test_local_manifest_requires_exact_pin_and_verified_artifact_bytes(checkout, monkeypatch):
    manifest = load_release_manifest(checkout, release_tag="v0.6.3")
    manifest["release"]["tag"] = "v0.0.1-local-check"
    manifest["manifest_sha256"] = sha256_bytes(canonical_json(
        {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    ))
    (checkout / "bocg-release-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ReleaseSnapshotError, match="unknown or mismatched"):
        load_release_manifest(checkout, release_tag=manifest["release"]["tag"])
    # The explicit pin selects the manifest, but no current files can stand in
    # for its historical artifacts without matching the original byte digests.
    failures = _scenario(checkout, monkeypatch, manifest_sha256=manifest["manifest_sha256"])
    assert any("pinned release artifact unavailable" in f for f in failures)
