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

    python3 tools/episode_surface.py specs/fixtures/episode-surface-synthetic.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

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


def _released_concepts(root: Path) -> dict[str, dict]:
    """Released concepts by identifier. Raises UNREADABLE when the file cannot be used."""
    concepts = _read_json(root / CONCEPTS_PATH)
    return {concept['concept_id']: concept for concept in concepts['concepts']}


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
    status = cell.get('status') if cell is not None else None
    return status if isinstance(status, str) and status in CELL_STATUSES else None


def _supports(point: dict, level: str, concepts: dict[str, dict], cells: set[str], root: Path) -> bool:
    """Whether a touchpoint names, at one level, a target that is reviewed in the release."""
    if level == 'division':
        return True
    if level == 'terminal_task':
        return bool(point.get('task_reference_id'))
    value = point.get(ID_FIELD_FOR_DEPTH[level])
    if level == 'control_point':
        return _cell_status(_cell(root, cells, value)) == REVIEWED_CELL
    concept = concepts.get(value) if isinstance(value, str) else None
    return isinstance(concept, dict) and concept.get('kind') == level and concept.get('review_status') == REVIEWED_CONCEPT


def _reviewed_evidence_depth(surface: dict, concepts: dict[str, dict], cells: set[str], root: Path) -> str:
    best = 'none'
    for point in surface.get('touchpoints') or []:
        if point.get('mapping_status') not in RATIFIED:
            continue
        # From the claimed depth downward: the first level with a reviewed target.
        for rank in range(depth_rank(point['depth']), depth_rank(best), -1):
            if _supports(point, DEPTH_ORDER[rank], concepts, cells, root):
                best = DEPTH_ORDER[rank]
                break
    return best


def reviewed_evidence_depth(surface: dict, root: Path = ROOT) -> str:
    """Deepest ratified depth whose target is itself reviewed in the release under `root`.

    A concept or cell that cannot be read from the release is never reviewed.
    """
    try:
        concepts = _released_concepts(root)
    except UNREADABLE:
        concepts = {}
    return _reviewed_evidence_depth(surface, concepts, _released_cells(root), root)


def surface_problems(surface: dict, *, root: Path = ROOT) -> list[str]:
    """Structural problems beyond JSON Schema: depth rules, release-bound identifiers and statuses."""
    problems: list[str] = []
    try:
        concepts = _read_json(root / CONCEPTS_PATH)
        concept_ids = {c['concept_id']: c for c in concepts['concepts']}
        concepts_digest = concepts['task_concepts_sha256']
    except UNREADABLE as exc:
        problems.append(f'{CONCEPTS_PATH} is not readable: {exc!r}')
    try:
        catalogue = _read_json(root / CATALOGUE_PATH)
        definitions = {d['reference_id']: d for d in catalogue['definitions']}
        divisions = {d['division_key'] for d in catalogue['definitions'] if d['kind'] == 'division'}
    except UNREADABLE as exc:
        problems.append(f'{CATALOGUE_PATH} is not readable: {exc!r}')
    if problems:
        return problems
    cells = _released_cells(root)
    release = surface.get('bocg_release') or {}
    if release.get('task_concepts_sha256') != concepts_digest:
        problems.append('surface is bound to a different task-concepts digest')
    for index, point in enumerate(surface.get('touchpoints') or []):
        where = f'touchpoint {index}'
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
            body = _cell(root, cells, cell)
            cell_status = _cell_status(body)
            if cell_status is None:
                problems.append(f'{where}: control_point_id names a cell whose status is not readable')
            elif status_key in point and point[status_key] != cell_status:
                problems.append(f'{where}: {status_key} is {cell_status} in the release')
            cell_division = body.get('division_key') if body is not None else None
            if cell_division in divisions and cell_division != division:
                problems.append(f'{where}: control_point_id belongs to another division')
    if surface.get('evidence_depth') != evidence_depth(surface):
        problems.append('evidence_depth does not follow the depth rule')
    if surface.get('candidate_depth') != candidate_depth(surface):
        problems.append('candidate_depth does not follow the depth rule')
    if 'reviewed_evidence_depth' in surface and (
            surface['reviewed_evidence_depth'] != _reviewed_evidence_depth(surface, concept_ids, cells, root)):
        problems.append('reviewed_evidence_depth does not follow the reviewed depth rule')
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    surface = json.loads(Path(argv[1]).read_text(encoding='utf-8'))
    problems = surface_problems(surface)
    for problem in problems:
        print('FAIL', problem)
    if not problems:
        print(
            f"evidence_depth={evidence_depth(surface)} candidate_depth={candidate_depth(surface)} "
            f"reviewed_evidence_depth={reviewed_evidence_depth(surface)}"
        )
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
