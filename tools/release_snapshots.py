"""Resolve release pins offline against verified, content-addressed snapshots.

Tags alone are resolved only through the reviewed snapshot index. An explicit
manifest digest may also select a valid local release manifest. Neither Git
history nor the mutable current catalogue supplies historical release evidence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

import jsonschema

from build_release_manifest import canonical_json, sha256_bytes

INDEX = "reference/release-snapshots/index.json"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ReleaseSnapshotError(ValueError):
    """A release or artifact cannot be verified against its declared pin."""


def _path(root: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or not relative or "\\" in relative
            or PurePosixPath(relative).is_absolute()
            or any(p in {"", ".", ".."} for p in relative.split("/"))):
        raise ReleaseSnapshotError(f"unsafe release artifact path: {relative!r}")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ReleaseSnapshotError(f"release artifact escapes its snapshot: {relative!r}")
    return path


def _reject_nonfinite(value: str) -> None:
    raise ReleaseSnapshotError(f"nonfinite JSON constant is not permitted: {value}")


def read_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ReleaseSnapshotError(f"unreadable release JSON {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseSnapshotError(f"{path.name} must contain a JSON object")
    return value


def validate_manifest(manifest: dict, *, root: Path) -> dict:
    """Check structure, unique paths, aggregate and self digest without mutation."""
    schema = read_json_object(root / "specs/bocg-release-manifest.schema.json")
    checker = required_format_checker()
    errors = list(jsonschema.Draft202012Validator(schema, format_checker=checker).iter_errors(manifest))
    if errors:
        raise ReleaseSnapshotError(f"release manifest schema: {errors[0].message[:180]}")
    artifacts = manifest["artifacts"]
    paths = [item["path"] for item in artifacts]
    if len(paths) != len(set(paths)):
        raise ReleaseSnapshotError("release manifest contains duplicate artifact paths")
    for relative in paths:
        _path(root, relative)
    if manifest["aggregate_sha256"] != sha256_bytes(canonical_json(artifacts)):
        raise ReleaseSnapshotError("release manifest aggregate digest mismatch")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest["manifest_sha256"] != sha256_bytes(canonical_json(unsigned)):
        raise ReleaseSnapshotError("release manifest self digest mismatch")
    profile = manifest["semantic_profile"]
    profile_artifact = next((a for a in artifacts if a["path"] == profile["path"]), None)
    if profile_artifact is None or profile_artifact["sha256"] != profile["sha256"]:
        raise ReleaseSnapshotError("release manifest semantic profile digest mismatch")
    return manifest


def required_format_checker() -> jsonschema.FormatChecker:
    checker = jsonschema.FormatChecker()
    if "date-time" not in checker.checkers:
        raise ReleaseSnapshotError("date-time validation requires jsonschema[format-nongpl]")
    return checker


def _index(root: Path) -> list[dict]:
    index = read_json_object(root / INDEX)
    entries = index.get("releases")
    if index.get("schema") != "bocg.release-snapshots/v1" or not isinstance(entries, list):
        raise ReleaseSnapshotError("invalid release snapshot index")
    tags, digests = set(), set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ReleaseSnapshotError("release snapshot index entry must be an object")
        tag = entry.get("tag")
        digest = entry.get("manifest_sha256")
        if not isinstance(tag, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", tag):
            raise ReleaseSnapshotError("invalid release tag in snapshot index")
        for field in ("manifest_sha256", "manifest_file_sha256"):
            if not isinstance(entry.get(field), str) or not SHA256.fullmatch(entry[field]):
                raise ReleaseSnapshotError(f"invalid {field} in snapshot index")
        if not isinstance(entry.get("commit_sha"), str) or not re.fullmatch(r"[0-9a-f]{40}", entry["commit_sha"]):
            raise ReleaseSnapshotError("invalid release commit in snapshot index")
        if tag in tags or digest in digests:
            raise ReleaseSnapshotError("ambiguous release snapshot index")
        tags.add(tag)
        digests.add(digest)
        if entry.get("snapshot_dir") != f"reference/release-snapshots/{tag}":
            raise ReleaseSnapshotError("release snapshot directory must match its tag")
        _path(root, entry["snapshot_dir"])
    return entries


def _resolve(root: Path, *, release_tag: str | None, manifest_sha256: str | None) -> tuple[dict, Path]:
    if release_tag is None and manifest_sha256 is None:
        raise ReleaseSnapshotError("an explicit release tag or manifest digest is required")
    if release_tag is not None and (not isinstance(release_tag, str) or not release_tag):
        raise ReleaseSnapshotError("release tag must be a nonempty string")
    if manifest_sha256 is not None and (not isinstance(manifest_sha256, str)
            or not SHA256.fullmatch(manifest_sha256) or manifest_sha256 == "0" * 64):
        raise ReleaseSnapshotError("manifest pin must be a nonzero SHA-256 digest")
    entries = _index(root)
    matches = [e for e in entries
               if (release_tag is None or e["tag"] == release_tag)
               and (manifest_sha256 is None or e["manifest_sha256"] == manifest_sha256)]
    if matches:
        entry = matches[0]
        artifact_root = _path(root, entry["snapshot_dir"])
        manifest_path = artifact_root / "bocg-release-manifest.json"
        try:
            body = manifest_path.read_bytes()
        except OSError as exc:
            raise ReleaseSnapshotError(f"release snapshot manifest unavailable: {exc}") from exc
        if sha256_bytes(body) != entry["manifest_file_sha256"]:
            raise ReleaseSnapshotError("release snapshot manifest file digest mismatch")
        manifest = validate_manifest(read_json_object(manifest_path), root=root)
        if (manifest["manifest_sha256"] != entry["manifest_sha256"]
                or manifest["release"]["tag"] != entry["tag"]
                or manifest["release"]["commit_sha"] != entry["commit_sha"]):
            raise ReleaseSnapshotError("release snapshot identity differs from its index")
        return manifest, artifact_root

    if release_tag is not None and any(e["tag"] == release_tag for e in entries):
        raise ReleaseSnapshotError(f"unknown or mismatched release pin: {release_tag}")
    # A mutable tag is insufficient to authorize a new local manifest. The
    # consumer must supply its exact content-addressed digest.
    local = root / "bocg-release-manifest.json"
    if manifest_sha256 is not None and local.is_file():
        manifest = validate_manifest(read_json_object(local), root=root)
        if any(e["tag"] == manifest["release"]["tag"]
               and e["manifest_sha256"] != manifest["manifest_sha256"] for e in entries):
            raise ReleaseSnapshotError("local manifest conflicts with an indexed release identity")
        if manifest["manifest_sha256"] == manifest_sha256 and (
            release_tag is None or manifest["release"]["tag"] == release_tag
        ):
            return manifest, root
    raise ReleaseSnapshotError(f"unknown or mismatched release pin: {release_tag or manifest_sha256}")


def load_release_manifest(root: Path, *, release_tag: str | None = None,
                          manifest_sha256: str | None = None) -> dict:
    return _resolve(root, release_tag=release_tag, manifest_sha256=manifest_sha256)[0]


def load_release_artifact(root: Path, artifact_path: str, *, release_tag: str | None = None,
                          manifest_sha256: str | None = None) -> bytes:
    manifest, artifact_root = _resolve(root, release_tag=release_tag, manifest_sha256=manifest_sha256)
    path = _path(artifact_root, artifact_path)
    record = next((a for a in manifest["artifacts"] if a["path"] == artifact_path), None)
    if record is None:
        raise ReleaseSnapshotError(f"artifact is not in the pinned release: {artifact_path}")
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise ReleaseSnapshotError(f"pinned release artifact unavailable: {artifact_path}") from exc
    if len(body) != record["size_bytes"] or sha256_bytes(body) != record["sha256"]:
        raise ReleaseSnapshotError(f"pinned release artifact digest mismatch: {artifact_path}")
    return body


def verified_archive_paths(root: Path) -> list[str]:
    """Verify every retained artifact before including the archive in a release."""
    paths = [INDEX]
    for entry in _index(root):
        manifest = load_release_manifest(root, release_tag=entry["tag"])
        retained = entry.get("retained_artifacts")
        if (not isinstance(retained, list) or not retained
                or any(not isinstance(p, str) for p in retained)
                or len(retained) != len(set(retained))):
            raise ReleaseSnapshotError("invalid retained-artifact list in snapshot index")
        required = {"reference/operating-catalogue.v1.json", "reference/task-concepts.v1.json"}
        required.update(a["path"] for a in manifest["artifacts"]
                        if a["path"].startswith("cells/") or a["path"].endswith("/matrix.json"))
        if not required <= set(retained):
            raise ReleaseSnapshotError("snapshot omits required catalogue, concepts, matrix or cells")
        paths.append(f"{entry['snapshot_dir']}/bocg-release-manifest.json")
        for relative in retained:
            load_release_artifact(root, relative, release_tag=entry["tag"])
            paths.append(f"{entry['snapshot_dir']}/{relative}")
    return sorted(paths)
