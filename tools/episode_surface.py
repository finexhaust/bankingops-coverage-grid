#!/usr/bin/env python3
"""SPEC-08 §3 episode-surface depth rule and release-bound reference checks.

A consumer computes an Episode's evidence depth from its touchpoints. The rule
is small enough to restate: the deepest touchpoint whose mapping status is
ratified (RATIFIED_MAPPING or QUALIFIED_MAPPING) sets `evidence_depth`; the
deepest PROPOSED or PENDING touchpoint sets `candidate_depth`. Rejected and
deferred touchpoints stay on the record and set neither. Candidates never raise
evidence depth. No touchpoints, or no ratified touchpoint, is depth `none`.

Both depths look only at the status of the mapping. `reviewed_evidence_depth`
also looks at the status of the thing mapped to: among ratified touchpoints, the
deepest level a touchpoint supports with a target that is itself reviewed in
the release. A control point counts only when its cell is CURATED, a function
or task concept only when it is REVIEWED. A division and a terminal task are
released labels with no review status of their own and count as they are. A
touchpoint whose target is unreviewed falls back to the deepest shallower level
it does support.

    python3 tools/episode_surface.py --current specs/fixtures/episode-surface-synthetic.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from release_snapshots import load_release_artifact, load_release_manifest

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS_PATH = 'reference/task-concepts.v1.json'
CATALOGUE_PATH = 'reference/operating-catalogue.v1.json'
DEPTH_ORDER = ('none', 'division', 'function_concept', 'task_concept', 'terminal_task', 'control_point')
RATIFIED = frozenset({'RATIFIED_MAPPING', 'QUALIFIED_MAPPING'})
CANDIDATE = frozenset({'PROPOSED', 'PENDING'})
ID_FIELD_FOR_DEPTH = {
    'function_concept': 'function_concept_id',
    'task_concept': 'task_concept_id',
    'terminal_task': 'task_reference_id',
    'control_point': 'control_point_id',
}
STATUS_FIELD_FOR_DEPTH = {
    'function_concept': 'function_concept_review_status',
    'task_concept': 'task_concept_review_status',
    'control_point': 'control_point_status',
}
CELL_STATUSES = ('PROPOSED', 'CURATED', 'RETIRED')
REVIEWED_CELL = 'CURATED'
REVIEWED_CONCEPT = 'REVIEWED'
# A release file that is absent, is not JSON or has another shape is unreadable.
UNREADABLE = (OSError, ValueError, LookupError, TypeError)


def depth_rank(depth: str) -> int:
    return DEPTH_ORDER.index(depth)


def deepest(touchpoints: list[dict], statuses: frozenset[str]) -> str:
    best = 'none'
    for point in touchpoints:
        if point.get('mapping_status') in statuses and depth_rank(point['depth']) > depth_rank(best):
            best = point['depth']
    return best


def evidence_depth(surface: dict) -> str:
    return deepest(surface.get('touchpoints') or [], RATIFIED)


def candidate_depth(surface: dict) -> str:
    return deepest(surface.get('touchpoints') or [], CANDIDATE)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding='utf-8'))


def _released_cells(root: Path) -> set[str]:
    return {path.stem for path in (root / 'cells').glob('*.json')}


def _cell(root: Path, cells: set[str], cell_id: object) -> dict | None:
    """The released cell an identifier names, or None when no readable cell file does."""
    if not isinstance(cell_id, str) or cell_id not in cells:
        return None
    try:
        cell = _read_json(root / 'cells' / f'{cell_id}.json')
    except UNREADABLE:
        return None
    return cell if isinstance(cell, dict) else None


def _cell_status(cell: dict | None) -> str | None:
    status = cell.get('status') if isinstance(cell, dict) else None
    return status if isinstance(status, str) and status in CELL_STATUSES else None


def _supports(point: dict, level: str, concepts: dict[str, dict], cells: dict[str, dict | None]) -> bool:
    """Whether a touchpoint names, at one level, a target that is reviewed in the release."""
    if level == 'division':
        return True
    if level == 'terminal_task':
        return bool(point.get('task_reference_id'))
    value = point.get(ID_FIELD_FOR_DEPTH[level])
    if level == 'control_point':
        return _cell_status(cells.get(value)) == REVIEWED_CELL
    concept = concepts.get(value) if isinstance(value, str) else None
    return isinstance(concept, dict) and concept.get('kind') == level and concept.get('review_status') == REVIEWED_CONCEPT


def _reviewed_evidence_depth(surface: dict, concepts: dict[str, dict], cells: dict[str, dict | None]) -> str:
    best = 'none'
    for point in surface.get('touchpoints') or []:
        if point.get('mapping_status') not in RATIFIED:
            continue
        # From the claimed depth downward: the first level with a reviewed target.
        for rank in range(depth_rank(point['depth']), depth_rank(best), -1):
            if _supports(point, DEPTH_ORDER[rank], concepts, cells):
                best = DEPTH_ORDER[rank]
                break
    return best


def reviewed_evidence_depth(surface: dict, root: Path = ROOT, *, current: bool = False) -> str:
    """Deepest ratified depth whose target is itself reviewed in the pinned release.

    A concept or cell that cannot be read from the release is never reviewed.
    """
    try:
        concepts, _, cells, _ = _release_data(surface, root, current)
        if surface['bocg_release']['task_concepts_sha256'] != concepts['task_concepts_sha256']:
            return 'none'
        concepts = {c['concept_id']: c for c in concepts['concepts']}
    except UNREADABLE:
        return 'none'
    return _reviewed_evidence_depth(surface, concepts, cells)


def _release_data(surface: dict, root: Path, current: bool) -> tuple[dict, dict, dict, str]:
    release = surface['bocg_release']
    if current:
        concepts = _read_json(root / CONCEPTS_PATH)
        catalogue = _read_json(root / CATALOGUE_PATH)
        cell_ids = _released_cells(root)
        cells = {c: _cell(root, cell_ids, c) for c in cell_ids}
    else:
        pin = {'release_tag': release['tag'], 'manifest_sha256': release['manifest_sha256']}
        manifest = load_release_manifest(root, **pin)
        concepts = json.loads(load_release_artifact(root, CONCEPTS_PATH, **pin))
        catalogue = json.loads(load_release_artifact(root, CATALOGUE_PATH, **pin))
        cells = {}
        for artifact in manifest['artifacts']:
            path = artifact['path']
            if path.startswith('cells/') and path.endswith('.json') and path.count('/') == 1:
                cell_id = Path(path).stem
                cells[cell_id] = None
        for point in surface.get('touchpoints') or []:
            cell_id = point.get('control_point_id')
            if isinstance(cell_id, str) and cell_id in cells:
                cells[cell_id] = json.loads(load_release_artifact(root, f'cells/{cell_id}.json', **pin))
    sources = catalogue['sources']
    paths = [s['path'] for s in sources if s['path'].startswith('live-run-') and s['path'].endswith('/matrix.json')]
    if len(paths) != 1:
        raise ValueError('catalogue must identify exactly one taxonomy run')
    run = paths[0].split('/')[0]
    if 'taxonomy_run' in release and release['taxonomy_run'] != run:
        raise ValueError(f'taxonomy run does not match pinned catalogue: {run}')
    return concepts, catalogue, cells, run


def surface_problems(surface: dict, *, root: Path = ROOT, current: bool = False) -> list[str]:
    """Structural problems beyond JSON Schema: depth rules, release-bound identifiers and statuses."""
    problems: list[str] = []
    try:
        concepts, catalogue, cells, _ = _release_data(surface, root, current)
        concept_ids = {c['concept_id']: c for c in concepts['concepts']}
        concepts_digest = concepts['task_concepts_sha256']
        definitions = {d['reference_id']: d for d in catalogue['definitions']}
        divisions = {d['division_key'] for d in catalogue['definitions'] if d['kind'] == 'division'}
    except UNREADABLE as exc:
        problems.append(f'pinned release is not readable: {exc!r}')
    if problems:
        return problems
    release = surface.get('bocg_release') or {}
    if release.get('task_concepts_sha256') != concepts_digest:
        problems.append('surface is bound to a different task-concepts digest')
    for index, point in enumerate(surface.get('touchpoints') or []):
        where = f'touchpoint {index}'
        if point.get('mapping_status') == 'SIGNIFICANT_UNMAPPED':
            if point.get('division_key') is not None:
                problems.append(f'{where}: significant unmapped touchpoint must not name a division')
            if point.get('depth') != 'none':
                problems.append(f'{where}: significant unmapped touchpoint must have depth none')
            if any(point.get(key) is not None for key in (
                'function_concept_id', 'task_concept_id', 'task_reference_id',
                'control_point_id', 'ruling',
            )):
                problems.append(f'{where}: significant unmapped touchpoint must not name a mapped target')
            continue
        division = point.get('division_key')
        if division not in divisions:
            problems.append(f'{where}: unknown division {division!r}')
        depth = point.get('depth')
        field = ID_FIELD_FOR_DEPTH.get(depth)
        if field and not point.get(field):
            problems.append(f'{where}: depth {depth} needs {field}')
        for key, kind in (('function_concept_id', 'function_concept'), ('task_concept_id', 'task_concept')):
            value = point.get(key)
            status_key = STATUS_FIELD_FOR_DEPTH[kind]
            if value is None:
                if status_key in point:
                    problems.append(f'{where}: {status_key} needs {key}')
                continue
            concept = concept_ids.get(value)
            if concept is None:
                problems.append(f'{where}: {key} is not a released concept')
            elif concept['kind'] != kind or concept['division_key'] != division:
                problems.append(f'{where}: {key} belongs to another kind or division')
            elif status_key in point and point[status_key] != concept['review_status']:
                problems.append(f"{where}: {status_key} is {concept['review_status']} in the release")
        task_ref = point.get('task_reference_id')
        if task_ref is not None:
            definition = definitions.get(task_ref)
            if definition is None or definition['kind'] != 'task' or definition['division_key'] != division:
                problems.append(f'{where}: task_reference_id is not a released task of the division')
            elif point.get('task_concept_id') in concept_ids:
                if task_ref not in concept_ids[point['task_concept_id']]['members']:
                    problems.append(f'{where}: task_reference_id is not a member of task_concept_id')
        cell = point.get('control_point_id')
        status_key = STATUS_FIELD_FOR_DEPTH['control_point']
        if cell is None:
            if status_key in point:
                problems.append(f'{where}: {status_key} needs control_point_id')
        elif cell not in cells:
            problems.append(f'{where}: control_point_id is not a released cell')
        else:
            body = cells[cell]
            cell_status = _cell_status(body)
            if cell_status is None:
                problems.append(f'{where}: control_point_id names a cell whose status is not readable')
            elif status_key in point and point[status_key] != cell_status:
                problems.append(f'{where}: {status_key} is {cell_status} in the release')
            cell_division = body.get('division_key') if isinstance(body, dict) else None
            if cell_division in divisions and cell_division != division:
                problems.append(f'{where}: control_point_id belongs to another division')
    if surface.get('evidence_depth') != evidence_depth(surface):
        problems.append('evidence_depth does not follow the depth rule')
    if surface.get('candidate_depth') != candidate_depth(surface):
        problems.append('candidate_depth does not follow the depth rule')
    if 'reviewed_evidence_depth' in surface and (
            surface['reviewed_evidence_depth'] != _reviewed_evidence_depth(surface, concept_ids, cells)):
        problems.append('reviewed_evidence_depth does not follow the reviewed depth rule')
    return problems


def main(argv: list[str]) -> int:
    current = len(argv) == 3 and argv[1] == '--current'
    if len(argv) != 2 and not current:
        print(__doc__)
        return 2
    surface = json.loads(Path(argv[-1]).read_text(encoding='utf-8'))
    problems = surface_problems(surface, current=current)
    for problem in problems:
        print('FAIL', problem)
    if not problems:
        concepts, _, cells, run = _release_data(surface, ROOT, current)
        concept_ids = {c['concept_id']: c for c in concepts['concepts']}
        current_run = _read_json(ROOT / 'reference/taxonomy-source.json')['run_dir']
        status = 'current' if run == current_run else 'historical'
        print(
            f"taxonomy_run={run} status={status}" + (" validation=checkout" if current else " validation=pinned") + " "
            f"evidence_depth={evidence_depth(surface)} candidate_depth={candidate_depth(surface)} "
            f"reviewed_evidence_depth={_reviewed_evidence_depth(surface, concept_ids, cells)}"
        )
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
