"""SPEC-08: task concepts, rulings and the episode surface."""
import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

from build_task_concepts import build_task_concepts, concept_id, machine_clusters, render, KINDS
from build_release_manifest import build_manifest, STATIC_ARTIFACTS
from episode_surface import candidate_depth, evidence_depth, reviewed_evidence_depth, surface_problems

ROOT = Path(__file__).parents[2]


def _concepts():
    return json.loads((ROOT / 'reference/task-concepts.v1.json').read_text())


def test_task_concepts_reproduce_and_validate():
    value = _concepts()
    assert render(build_task_concepts(ROOT)) == (ROOT / 'reference/task-concepts.v1.json').read_text()
    schema = json.loads((ROOT / 'specs/task-concepts.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    assert not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value))
    assert value['institution_instances'] is False
    assert value['method']['machine']['read_by_a_human'] is False


def test_every_released_definition_belongs_to_exactly_one_concept_of_its_division():
    value = _concepts()
    catalogue = json.loads((ROOT / 'reference/operating-catalogue.v1.json').read_text())
    released = {d['reference_id']: d for d in catalogue['definitions'] if d['kind'] in KINDS}
    seen = []
    for concept in value['concepts']:
        for member in concept['members']:
            assert released[member]['division_key'] == concept['division_key']
            assert KINDS[released[member]['kind']] == concept['kind']
            seen.append(member)
    assert sorted(seen) == sorted(released)
    assert len({c['concept_id'] for c in value['concepts']}) == len(value['concepts'])


def test_current_task_concepts_use_machine_provenance_without_reviewed_rulings():
    value = _concepts()
    reviewed = [d for d in value['divisions'] if d['review_status'] == 'REVIEWED']
    assert reviewed == []
    assert value['counts']['reviewed_divisions'] == 0
    assert value['counts']['auto_divisions'] == len(value['divisions'])
    assert value['counts']['reviewed_aliases'] == 0


def test_auto_divisions_are_machine_clustered_and_never_claim_review():
    value = _concepts()
    for division in value['divisions']:
        if division['review_status'] == 'AUTO':
            assert division['ruling'] is None and division['basis'] == 'machine_clustered'
    for concept in value['concepts']:
        if concept['review_status'] == 'AUTO':
            assert concept['basis'] == 'machine_clustered' and concept['label_source'] == 'member'
            assert concept['label'] in concept['member_labels']
            assert all('unread by any human' in a['rationale'] for a in concept['aliases'])


def test_machine_clustering_is_deterministic_and_never_invents_a_label():
    labels = ['report corporate bond trade to trace within 15 minute', 'report us corporate bond trade to trace within required window', 'price a cash bond or credit derivative']
    first = machine_clusters(labels)
    assert first == machine_clusters(list(reversed(labels)))
    assert any(len(group) == 2 for group in first)
    assert {label for group in first for label in group} == set(labels)


def test_concept_identity_separates_kind_division_and_label():
    assert concept_id('task_concept', 'a', 'x') != concept_id('function_concept', 'a', 'x')
    assert concept_id('task_concept', 'a', 'x') != concept_id('task_concept', 'b', 'x')
    assert concept_id('task_concept', 'a', 'x') != concept_id('task_concept', 'a', 'X')


def test_ruling_rejects_unknown_members_and_missing_rationales(tmp_path):
    import shutil
    for relative in ('reference/operating-catalogue.v1.json', 'reference/task-concept-rulings.yaml'):
        dest = tmp_path / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    rulings_path = tmp_path / 'reference/task-concept-rulings.yaml'
    catalogue = json.loads((tmp_path / 'reference/operating-catalogue.v1.json').read_text())
    division = next(d['division_key'] for d in catalogue['definitions'] if d['kind'] == 'division')
    members = [
        d['label'] for d in catalogue['definitions']
        if d['kind'] == 'task' and d['division_key'] == division
    ][:2]
    original = yaml.safe_load(rulings_path.read_text())
    original['rulings'] = [{
        'division_key': division,
        'review_status': 'REVIEWED',
        'ruled_by': 'test reviewer',
        'ruled_at': '2026-10-29',
        'basis': 'synthetic test ruling',
        'concepts': [{
            'kind': 'task_concept',
            'label': members[0],
            'members': members,
            'rationale': 'synthetic test rationale',
            'alias_rationales': {members[1]: 'synthetic alias rationale'},
        }],
    }]
    broken = copy.deepcopy(original)
    broken['rulings'][0]['concepts'][0]['members'].append('not a released task')
    rulings_path.write_text(yaml.safe_dump(broken, sort_keys=False))
    with pytest.raises(ValueError, match='not a released'):
        build_task_concepts(tmp_path)
    broken = copy.deepcopy(original)
    broken['rulings'][0]['concepts'][0]['alias_rationales'].pop(members[1])
    rulings_path.write_text(yaml.safe_dump(broken, sort_keys=False))
    with pytest.raises(ValueError, match='rationale'):
        build_task_concepts(tmp_path)
    broken = copy.deepcopy(original)
    broken['rulings'][0]['review_status'] = 'AUTO'
    rulings_path.write_text(yaml.safe_dump(broken, sort_keys=False))
    with pytest.raises(ValueError, match='REVIEWED'):
        build_task_concepts(tmp_path)


def test_episode_surface_fixture_follows_depth_rule_and_release_binding():
    schema = json.loads((ROOT / 'specs/episode-surface.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    fixture = json.loads((ROOT / 'specs/fixtures/episode-surface-synthetic.json').read_text())
    assert not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(fixture))
    assert surface_problems(fixture, root=ROOT, current=True) == []
    assert evidence_depth(fixture) == fixture['evidence_depth']
    assert candidate_depth(fixture) == fixture['candidate_depth']


def test_candidates_never_raise_evidence_depth():
    fixture = json.loads((ROOT / 'specs/fixtures/episode-surface-synthetic.json').read_text())
    for point in fixture['touchpoints']:
        if point['mapping_status'] in {'RATIFIED_MAPPING', 'QUALIFIED_MAPPING'}:
            point['mapping_status'] = 'PROPOSED'
            point['ruling'] = None
    assert evidence_depth(fixture) == 'none'
    assert candidate_depth(fixture) != 'none'
    assert 'evidence_depth does not follow the depth rule' in surface_problems(fixture, root=ROOT, current=True)


def test_surface_rejects_identifiers_outside_the_release():
    fixture = json.loads((ROOT / 'specs/fixtures/episode-surface-synthetic.json').read_text())
    point = next(p for p in fixture['touchpoints'] if p['task_concept_id'])
    point['task_concept_id'] = 'task_concept:' + point['division_key'] + ':' + '0' * 24
    assert any('not a released concept' in p for p in surface_problems(fixture, root=ROOT, current=True))


def _historical_surface():
    base = ROOT / 'reference/release-snapshots/v0.6.3/reference'
    concepts = json.loads((base / 'task-concepts.v1.json').read_text())
    concept = next(c for c in concepts['concepts'] if c['kind'] == 'task_concept' and c['members'])
    return {
        'schema': 'bocg.episode-surface/v1',
        'bocg_release': {
            'tag': 'v0.6.3',
            'manifest_sha256': 'a157ff3e9bff43dee9857c889c57f5ce87917e530999fbd6d365f47dfaf352ec',
            'task_concepts_sha256': concepts['task_concepts_sha256'],
            'taxonomy_run': 'live-run-20260826',
        },
        'episode_ref': 'ep-000000000001',
        'source_profile_ref': 'sp-00000000',
        'touchpoints': [{
            'division_key': concept['division_key'],
            'depth': 'terminal_task',
            'mapping_status': 'RATIFIED_MAPPING',
            'function_concept_id': None,
            'task_concept_id': concept['concept_id'],
            'task_reference_id': concept['members'][0],
            'control_point_id': None,
            'ruling': {'ruled_at': '2026-09-24', 'ruled_by_role': 'owner'},
        }],
        'evidence_depth': 'terminal_task',
        'candidate_depth': 'none',
        'reviewed_evidence_depth': 'terminal_task',
    }


def test_historical_surface_uses_pinned_run_and_cli_reports_it(tmp_path):
    import subprocess
    import sys
    surface = _historical_surface()
    schema = json.loads((ROOT / 'specs/episode-surface.schema.json').read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(surface)
    assert surface_problems(surface) == []
    path = tmp_path / 'surface.json'
    path.write_text(json.dumps(surface))
    result = subprocess.run([sys.executable, str(ROOT / 'tools/episode_surface.py'), str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'taxonomy_run=live-run-20260826 status=historical validation=pinned' in result.stdout
    del surface['bocg_release']['taxonomy_run']
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(surface)
    assert surface_problems(surface) == []
    path.write_text(json.dumps(surface))
    result = subprocess.run([sys.executable, str(ROOT / 'tools/episode_surface.py'), str(path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'taxonomy_run=live-run-20260826 status=historical' in result.stdout


def test_historical_surface_rejects_mismatched_pin_run_and_identifiers():
    surface = _historical_surface()
    for field, value in [('tag', 'v0.6.2'), ('manifest_sha256', '0' * 64),
                         ('taxonomy_run', 'live-run-20261019'), ('task_concepts_sha256', '0' * 64)]:
        broken = copy.deepcopy(surface)
        broken['bocg_release'][field] = value
        assert surface_problems(broken), field
    assert reviewed_evidence_depth(broken) == 'none'
    broken = copy.deepcopy(surface)
    broken['touchpoints'][0]['task_reference_id'] = 'task:' + broken['touchpoints'][0]['division_key'] + ':' + '0' * 24
    assert any('not a released task' in p for p in surface_problems(broken))


def test_historical_surface_rejects_tampered_snapshot(tmp_path):
    import shutil
    shutil.copytree(ROOT / 'reference/release-snapshots', tmp_path / 'reference/release-snapshots')
    (tmp_path / 'specs').mkdir()
    shutil.copyfile(ROOT / 'specs/bocg-release-manifest.schema.json', tmp_path / 'specs/bocg-release-manifest.schema.json')
    path = tmp_path / 'reference/release-snapshots/v0.6.3/reference/operating-catalogue.v1.json'
    path.write_text(path.read_text() + ' ')
    assert any('digest mismatch' in p for p in surface_problems(_historical_surface(), root=tmp_path))


def test_historical_cell_is_verified_and_reviewed_in_its_release(tmp_path):
    import shutil
    surface = _historical_surface()
    surface['touchpoints'] = [{
        'division_key': 'trade_lifecycle_operations', 'depth': 'control_point',
        'mapping_status': 'RATIFIED_MAPPING', 'function_concept_id': None,
        'task_concept_id': None, 'task_reference_id': None,
        'control_point_id': 'cp_otc_confirmation_timeliness', 'control_point_status': 'PROPOSED',
        'ruling': {'ruled_at': '2026-09-24', 'ruled_by_role': 'owner'},
    }]
    surface['evidence_depth'] = 'control_point'
    surface['reviewed_evidence_depth'] = 'division'
    assert surface_problems(surface) == []
    surface['touchpoints'][0]['control_point_status'] = 'CURATED'
    assert any('PROPOSED in the release' in p for p in surface_problems(surface))
    surface['touchpoints'][0]['control_point_status'] = 'PROPOSED'
    shutil.copytree(ROOT / 'reference/release-snapshots', tmp_path / 'reference/release-snapshots')
    (tmp_path / 'specs').mkdir()
    shutil.copyfile(ROOT / 'specs/bocg-release-manifest.schema.json', tmp_path / 'specs/bocg-release-manifest.schema.json')
    cell = tmp_path / 'reference/release-snapshots/v0.6.3/cells/cp_otc_confirmation_timeliness.json'
    cell.unlink()
    assert any('artifact unavailable' in p for p in surface_problems(surface, root=tmp_path))


def test_release_binds_concepts_and_refuses_stale_concepts(tmp_path):
    import hashlib
    import shutil
    manifest = build_manifest(tag='v0.6.0', commit_sha='a' * 40, generated_at='2026-09-24T00:00:00Z', root=ROOT)
    rows = {row['path']: row for row in manifest['artifacts']}
    for path in ('specs/SPEC-08-task-concepts-and-episode-surface.md', 'specs/task-concepts.schema.json', 'specs/episode-surface.schema.json', 'reference/task-concepts.v1.json', 'reference/task-concept-rulings.yaml', 'specs/fixtures/episode-surface-synthetic.json'):
        assert path in STATIC_ARTIFACTS
        assert rows[path]['sha256'] == hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    for path in STATIC_ARTIFACTS:
        dest = tmp_path / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, dest)
    shutil.copyfile(ROOT / 'reference/taxonomy-source.json', tmp_path / 'reference/taxonomy-source.json')
    shutil.copytree(ROOT / 'live-run-20261019', tmp_path / 'live-run-20261019')
    shutil.copytree(ROOT / 'cells', tmp_path / 'cells')
    concepts = tmp_path / 'reference/task-concepts.v1.json'
    value = json.loads(concepts.read_text())
    value['concepts'][0]['label'] = 'Unreviewed change'
    concepts.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='task concepts'):
        build_manifest(tag='v0.6.0', commit_sha='a' * 40, generated_at='2026-09-24T00:00:00Z', root=tmp_path)
