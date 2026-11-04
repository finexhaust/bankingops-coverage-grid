#!/usr/bin/env python3
"""Build BOCG's proposed financial-work context from public taxonomy snapshots.

No model calls, occurrence data, benchmark positions or seller coverage are inputs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSALS = 'reference/financial-work-context-proposals.v1.json'
OUTPUT = 'reference/financial-work-context.v1.json'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def build_context(root=ROOT):
    proposal_bytes = (root / PROPOSALS).read_bytes()
    proposals = json.loads(proposal_bytes)
    snapshots, areas, sources = [], {}, [{'path': PROPOSALS, 'sha256': digest(proposal_bytes)}]
    for definition in proposals['snapshots']:
        raw = (root / definition['path']).read_bytes()
        matrix = json.loads(raw)
        rows = {r['division_key']: r for r in matrix['rows']}
        if set(rows) != set(matrix['division_keys']) or len(rows) != len(matrix['division_keys']):
            raise ValueError('Inconsistent public matrix: ' + definition['path'])
        source = {**definition, 'sha256': digest(raw), 'area_count': len(rows)}
        snapshots.append(source)
        sources.append({'path': definition['path'], 'sha256': source['sha256']})
        for key, row in sorted(rows.items()):
            area = areas.setdefault(key, {'reference_id': 'division:'+key, 'division_key': key,
                'labels_by_snapshot': {}, 'snapshot_bindings': []})
            area['labels_by_snapshot'][definition['id']] = sorted(set(row['names']))
            area['snapshot_bindings'].append({'snapshot_id': definition['id'],
                'matrix_sha256': source['sha256'], 'source_status': definition['source_status']})
    domain_ids = {d['reference_id'] for d in proposals['domains']}
    if len(domain_ids) != len(proposals['domains']):
        raise ValueError('Duplicate context domain identifier')
    for domain in proposals['domains']:
        if domain['broader'] and domain['broader'] not in domain_ids:
            raise ValueError('Unknown broader context: ' + domain['broader'])
        visited = {domain['reference_id']}; cursor = domain['broader']
        while cursor:
            if cursor in visited:
                raise ValueError('Context hierarchy cycle')
            visited.add(cursor)
            cursor = next(d['broader'] for d in proposals['domains'] if d['reference_id'] == cursor)
    current = next(s['id'] for s in snapshots if s['role'] == 'current_generation')
    for key, area in areas.items():
        placement = proposals['area_placements'].get(key)
        area.update(label=placement['label'] if placement else key.replace('_', ' '),
                    domain_links=[], context_status='PROPOSED' if placement else 'PENDING',
                    current_presence='present' if current in area['labels_by_snapshot'] else 'historical_only')
        if placement:
            for domain in placement['domains']:
                if domain not in domain_ids:
                    raise ValueError('Unknown contextual domain: ' + domain)
                area['domain_links'].append({'reference_id': domain, 'relation': 'skos:broader',
                    'status': 'PROPOSED', 'basis': placement['basis']})
        # Absence in a later run has no retirement, identity or equivalence semantics.
        area['absence_means_retired'] = False
    stale = sorted(set(proposals['area_placements']) - set(areas))
    if stale:
        raise ValueError('Context proposal has no public snapshot binding: ' + ', '.join(stale))
    context = {'schema': 'bocg.financial-work-context/v1', 'version': proposals['version'],
        'status': 'PROPOSED', 'root_ref': 'domain:institutional_finance',
        'public_definitions_only': True, 'institution_instances': False,
        'method': proposals['method'], 'semantics': proposals['semantics'],
        'sources': sources, 'snapshots': snapshots, 'domains': proposals['domains'],
        'capabilities': proposals['capabilities'], 'areas': [areas[k] for k in sorted(areas)],
        'counts': {'areas': len(areas), 'domains': len(domain_ids)-1,
            'capabilities': len(proposals['capabilities']),
            'current_areas': sum(a['current_presence']=='present' for a in areas.values()),
            'historical_only_areas': sum(a['current_presence']=='historical_only' for a in areas.values()),
            'unplaced_areas': sum(not a['domain_links'] for a in areas.values())}}
    context['context_sha256'] = digest(canonical(context))
    return context


def verify_context(context):
    body = {k:v for k,v in context.items() if k != 'context_sha256'}
    if digest(canonical(body)) != context['context_sha256']:
        raise ValueError('Context digest differs from its content')
    return context


def resolve_area(context, division_key):
    """Unknown areas survive as unresolved; they never vanish from the funnel."""
    verify_context(context)
    area = next((a for a in context['areas'] if a['division_key']==division_key), None)
    if area is None:
        return {'division_key': division_key, 'resolved': False, 'context_status': 'PENDING',
                'domain_links': [], 'snapshot_bindings': []}
    return {'resolved': True, **area}


def project_placement(context, placement):
    """Resolve a consumer sidecar without promoting any of its evidence claims."""
    verify_context(context)
    if placement['context_binding'] != {'version': context['version'], 'context_sha256': context['context_sha256']}:
        raise ValueError('Consumer placement names a different context revision')
    capabilities = {c['reference_id']: c for c in context['capabilities']}
    areas = [{**t, 'context': resolve_area(context, t['division_key'])} for t in placement['area_touchpoints']]
    links = []
    for touch in placement['capability_touchpoints']:
        ref = touch['capability_ref']
        if ref not in capabilities:
            raise ValueError('Unknown capability reference: ' + ref)
        links.append({**touch, 'definition': capabilities[ref]})
    return {'schema': 'bocg.financial-work-projection/v1', 'subject_ref': placement['subject_ref'],
        'subject_kind': placement['subject_kind'], 'context_binding': placement['context_binding'],
        'area_touchpoints': areas, 'capability_touchpoints': links,
        'mapping_statuses_preserved': True, 'coverage_promotion': False,
        'context_increases_evidence_depth': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / OUTPUT)
    parser.add_argument('--resolve', metavar='DIVISION_KEY')
    parser.add_argument('--project', type=Path, help='Consumer-owned context-placement JSON; never copied into the public catalogue')
    args = parser.parse_args()
    context = build_context()
    if args.resolve:
        print(json.dumps(resolve_area(context, args.resolve), indent=2, ensure_ascii=False))
    elif args.project:
        # Validate the actual consumer document, not synthetic fixtures or tests.
        import jsonschema
        placement = json.loads(args.project.read_text())
        schema = json.loads((ROOT / 'specs/financial-work-placement.schema.json').read_text())
        jsonschema.Draft202012Validator(schema).validate(placement)
        print(json.dumps(project_placement(context, placement), indent=2, ensure_ascii=False))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(context, indent=2, ensure_ascii=False)+'\n')
        print(json.dumps({'file': str(args.output), 'version': context['version'],
                          'status': context['status'], **context['counts'], 'context_sha256': context['context_sha256']}))


if __name__ == '__main__':
    main()
