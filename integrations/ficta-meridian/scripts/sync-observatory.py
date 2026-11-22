#!/usr/bin/env python3
"""Generate or apply the static Meridian observatory data blocks."""
from __future__ import annotations

import argparse
import json
import os
import stat
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OBSERVATORY_PATH = ROOT / "reference/public-eval-observatory.v1.json"
SEED_PATH = ROOT / "integrations/ficta-meridian/app/data/public-eval-observatory.ts"


def load_observatory() -> dict:
    observatory = json.loads(OBSERVATORY_PATH.read_text(encoding="utf-8"))
    if observatory.get("schema") != "bocg.public-eval-observatory/v1":
        raise ValueError("unexpected public-eval observatory schema")
    if not isinstance(observatory.get("cleanroom_eval"), dict):
        raise ValueError("observatory has no cleanroom_eval block")
    llmaj = observatory.get("llmaj")
    if not isinstance(llmaj, dict) or not isinstance(llmaj.get("cases"), list):
        raise ValueError("observatory has no llmaj cases")
    return observatory


def public_eval_block(observatory: dict) -> dict:
    return {
        "prereg_sha256": observatory["prereg_sha256"],
        "headline": observatory["llmaj"]["headline"],
        "llmaj": observatory["llmaj"],
        "overlay_paint": observatory["overlay_paint"],
        "observatory_sha256": observatory["observatory_sha256"],
        "source": "bocg.public-eval-observatory/v1",
    }


def render_seed(observatory: dict) -> str:
    return (
        "// GENERATED from reference/public-eval-observatory.v1.json; do not hand-edit.\n"
        f"export const CLEANROOM_EVAL_PIN = {json.dumps(observatory['cleanroom_eval'], indent=2, ensure_ascii=False)} as const;\n"
        f"export const PUBLIC_EVAL_OBSERVATORY = {json.dumps(public_eval_block(observatory), indent=2, ensure_ascii=False)} as const;\n"
    )


def sync_seed(*, check: bool) -> int:
    expected = render_seed(load_observatory())
    if check:
        if not SEED_PATH.is_file() or SEED_PATH.read_text(encoding="utf-8") != expected:
            print(f"FAIL {SEED_PATH.relative_to(ROOT)} is stale; run sync-observatory.py --write")
            return 1
        print("ok Meridian seed matches the observatory")
        return 0
    SEED_PATH.write_text(expected, encoding="utf-8")
    print(f"wrote {SEED_PATH.relative_to(ROOT)}")
    return 0


def apply_manifest(path: Path) -> int:
    observatory = load_observatory()
    manifest_path = path.resolve(strict=True)
    if not manifest_path.is_file():
        raise ValueError(f"consumer manifest is not a file: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("consumer manifest must be a JSON object")

    updated = dict(manifest)
    updated["cleanroom_eval"] = observatory["cleanroom_eval"]
    updated["public_eval"] = public_eval_block(observatory)
    encoded = json.dumps(updated, indent=2, ensure_ascii=False) + "\n"

    mode = stat.S_IMODE(manifest_path.stat().st_mode)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=manifest_path.parent,
            prefix=f".{manifest_path.name}.",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(encoded)
            temporary.flush()
            os.fsync(temporary.fileno())
        temporary_path.chmod(mode)
        os.replace(temporary_path, manifest_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(f"updated cleanroom_eval and public_eval in {manifest_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    group.add_argument("--apply-manifest", type=Path)
    args = parser.parse_args()
    if args.apply_manifest is not None:
        return apply_manifest(args.apply_manifest)
    return sync_seed(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
