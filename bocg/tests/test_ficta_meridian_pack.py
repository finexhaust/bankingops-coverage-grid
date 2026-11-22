import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[2]
APPLY_SCRIPT = ROOT / "integrations/ficta-meridian/apply-to-finexhaust.sh"
OBSERVATORY_PATH = ROOT / "reference/public-eval-observatory.v1.json"


def test_seed_generator_check_and_observatory_cases_match():
    result = subprocess.run(
        [
            sys.executable,
            os.fspath(ROOT / "integrations/ficta-meridian/scripts/sync-observatory.py"),
            "--check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    seed = (
        ROOT / "integrations/ficta-meridian/app/data/public-eval-observatory.ts"
    ).read_text(encoding="utf-8")
    observatory = json.loads(OBSERVATORY_PATH.read_text(encoding="utf-8"))

    def exported_value(name):
        prefix = f"export const {name} = "
        start = seed.index(prefix) + len(prefix)
        end = seed.index(" as const;", start)
        return json.loads(seed[start:end])

    public_eval = exported_value("PUBLIC_EVAL_OBSERVATORY")
    assert public_eval["llmaj"]["cases"] == observatory["llmaj"]["cases"]
    assert exported_value("CLEANROOM_EVAL_PIN") == observatory["cleanroom_eval"]


def test_apply_preserves_manifest_fields_and_updates_only_data_blocks(tmp_path):
    manifest_path = tmp_path / "ficta-meridian-site/manifests/latest.json"
    manifest_path.parent.mkdir(parents=True)
    original = {
        "schema": "ficta-meridian.public-release-observatory/v3",
        "built_at": "2026-11-22T00:00:00Z",
        "bocg": {"tag": "v1.0.0"},
        "cleanroom_eval": {"version": "old"},
        "public_eval": {"llmaj": {"cases": []}},
        "consumer_owned_field": {"keep": True},
    }
    manifest_path.write_text(json.dumps(original) + "\n", encoding="utf-8")
    env = {**os.environ, "BOCG_ROOT": os.fspath(ROOT)}

    result = subprocess.run(
        ["bash", os.fspath(APPLY_SCRIPT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    observatory = json.loads(OBSERVATORY_PATH.read_text(encoding="utf-8"))
    assert updated["cleanroom_eval"] == observatory["cleanroom_eval"]
    assert updated["public_eval"]["llmaj"]["cases"] == observatory["llmaj"]["cases"]
    assert updated["public_eval"]["llmaj"]["cases"][1]["sensitivity_promotion"] == "UNCERTAIN"
    assert {
        key: value
        for key, value in updated.items()
        if key not in {"cleanroom_eval", "public_eval"}
    } == {
        key: value
        for key, value in original.items()
        if key not in {"cleanroom_eval", "public_eval"}
    }


def test_apply_rejects_invalid_manifest_without_modifying_it(tmp_path):
    manifest_path = tmp_path / "ficta-meridian-site/manifests/latest.json"
    manifest_path.parent.mkdir(parents=True)
    original = b'{"bocg":\n'
    manifest_path.write_bytes(original)
    env = {**os.environ, "BOCG_ROOT": os.fspath(ROOT)}

    result = subprocess.run(
        ["bash", os.fspath(APPLY_SCRIPT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert manifest_path.read_bytes() == original
    assert sorted(path.name for path in manifest_path.parent.iterdir()) == ["latest.json"]
