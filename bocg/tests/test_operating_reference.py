import copy
import hashlib
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator, FormatChecker
from build_operating_catalogue import build_catalogue, reference_id
from build_release_manifest import build_manifest, STATIC_ARTIFACTS
from gate_conformance import financial_context_version_problems

ROOT = Path(__file__).parents[2]

def test_catalogue_reproduces_public_sources_without_instances():
    value = json.loads((ROOT / 'reference/operating-catalogue.v1.json').read_text())
    assert build_catalogue(ROOT) == value
    assert value['institution_instances'] is False
    assert len({d['reference_id'] for d in value['definitions']}) == len(value['definitions'])
    assert sum(d['kind'] == 'division' for d in value['definitions']) == 25
    for source in value['sources']:
        assert hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest() == source['sha256']

def test_reference_identity_keeps_divisions_and_kinds_separate():
    assert reference_id('task', 'rates', 'price') != reference_id('function', 'rates', 'price')
    assert reference_id('task', 'rates', 'price') != reference_id('task', 'credit', 'price')
    assert reference_id('task', 'rates', 'price') != reference_id('task', 'rates', 'Price')
    assert reference_id('division', 'rates') == 'division:rates'

def test_register_schema_is_valid_and_review_is_explicit():
    schema = json.loads((ROOT / 'specs/operating-unit-register.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    review_schema = schema['$defs']['review']
    validator = Draft202012Validator(review_schema)
    assert list(validator.iter_errors({'status':'REVIEWED','reviewer_ref':None,'reviewed_at':None,'reason':'Source review','assertion_basis':'source_observed'}))
    assert not list(validator.iter_errors({'status':'PROPOSED','reviewer_ref':None,'reviewed_at':None,'reason':'Source candidate','assertion_basis':'inferred'}))

def test_register_preserves_observed_and_proposed_reporting_relations():
    schema = json.loads((ROOT / 'specs/operating-unit-register.schema.json').read_text())
    review = {'status':'PROPOSED','reviewer_ref':None,'reviewed_at':None,'reason':'Source candidate','assertion_basis':'source_observed'}
    register = {
        'schema':'bocg.operating-unit-register/v1',
        'contract_version':'1.1.0',
        'dataset_id':'register-1',
        'revision':1,
        'previous_sha256':None,
        'tenant_id':'tenant-1',
        'plane':'record',
        'owner_ref':'owner-1',
        'recorded_at':'2026-11-22T00:00:00Z',
        'bocg':{'release_tag':'v0.4.0','manifest_sha256':'a'*64,'catalogue_sha256':'b'*64,'contract_version':'1.1.0'},
        'sources':[{'source_id':'attestation-1','kind':'sme_attestation','locator':'private:source','sha256':'c'*64,'observed_at':None}],
        'units':[],
        'assignments':[],
        'relationships':[],
        'role_holdings':[{
            'role_holding_id':'holding-1','person_ref':'person-1','organization_ref':'org-1',
            'unit_id':None,'role_ref':'role-1','title':'Vice President','grade':'G8','seniority':'Senior',
            'valid_from':None,'valid_to':None,'corrects_role_holding_id':None,
            'evidence_refs':['attestation-1'],'review':review,
        }],
        'reporting_relations':[
            {'reporting_relation_id':'line-observed','manager_person_ref':'person-1','report_person_ref':'person-2',
             'status':'observed','valid_from':None,'valid_to':None,'corrects_reporting_relation_id':None,
             'evidence_refs':['attestation-1'],'review':review},
            {'reporting_relation_id':'line-proposed','manager_person_ref':'person-3','report_person_ref':'person-2',
             'status':'proposed','valid_from':None,'valid_to':None,'corrects_reporting_relation_id':None,
             'evidence_refs':['attestation-1'],'review':review},
        ],
        'regulated_function_correspondences':[{
            'correspondence_id':'correspondence-1','role_holding_id':'holding-1',
            'regulated_function_ref':'regulated-function-1','functional_confidence':'medium',
            'legal_applicability':'unknown','registration_status':'unknown',
            'registration_ref':None,'jurisdiction':None,'evidence_refs':['attestation-1'],'review':review,
        }],
        'settings':[],
    }
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(register))
    assert not errors, [error.message for error in errors]
    assert [row['status'] for row in register['reporting_relations']] == ['observed', 'proposed']
    assert register['role_holdings'][0]['valid_from'] is None

def test_corrected_reporting_relation_requires_correction_lineage():
    schema = json.loads((ROOT / 'specs/operating-unit-register.schema.json').read_text())
    relation_schema = dict(schema['$defs']['reporting_relation'])
    relation_schema['$defs'] = schema['$defs']
    validator = Draft202012Validator(relation_schema)
    relation = {
        'reporting_relation_id':'line-corrected','manager_person_ref':'person-1','report_person_ref':'person-2',
        'status':'corrected','valid_from':None,'valid_to':None,'corrects_reporting_relation_id':None,
        'evidence_refs':['source-1'],
        'review':{'status':'PROPOSED','reviewer_ref':None,'reviewed_at':None,'reason':'Correction','assertion_basis':'corrected'},
    }
    assert list(validator.iter_errors(relation))
    relation['corrects_reporting_relation_id'] = 'line-prior'
    assert not list(validator.iter_errors(relation))

def test_context_version_gate_uses_proposal_version(tmp_path):
    import shutil
    assert financial_context_version_problems(ROOT) == []
    paths = (
        'reference/financial-work-context-proposals.v1.json',
        'reference/financial-work-context.v1.json',
        'specs/operating-reference-contract.json',
        'specs/common-semantic-profile.yaml',
        'specs/SPEC-10-financial-work-context.md',
    )
    for path in paths:
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, destination)
    contract_path = tmp_path / 'specs/operating-reference-contract.json'
    contract = json.loads(contract_path.read_text())
    contract['optional_context']['version'] = '0.1.0'
    contract_path.write_text(json.dumps(contract))
    problems = financial_context_version_problems(tmp_path)
    assert len(problems) == 1
    assert 'operating-reference-contract.json declares' in problems[0]

def test_release_binds_contract_schema_and_reproducible_catalogue():
    manifest = build_manifest(tag='v0.4.0', commit_sha='a'*40, generated_at='2026-09-08T00:00:00Z', root=ROOT)
    rows = {row['path']:row for row in manifest['artifacts']}
    for path in ('specs/operating-reference-contract.json','specs/operating-unit-register.schema.json','reference/operating-catalogue.v1.json'):
        assert path in STATIC_ARTIFACTS
        assert rows[path]['sha256'] == hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def test_stale_catalogue_blocks_release(tmp_path):
    import shutil
    for path in STATIC_ARTIFACTS:
        dest=tmp_path/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
    shutil.copyfile(ROOT/'reference/taxonomy-source.json',tmp_path/'reference/taxonomy-source.json')
    shutil.copytree(ROOT/'live-run-20261019',tmp_path/'live-run-20261019')
    shutil.copytree(ROOT/'cells',tmp_path/'cells')
    catalogue=tmp_path/'reference/operating-catalogue.v1.json'
    value=json.loads(catalogue.read_text());value['definitions'][0]['label']='Unreviewed change';catalogue.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='catalogue'):
        build_manifest(tag='v0.4.0',commit_sha='a'*40,generated_at='2026-09-08T00:00:00Z',root=tmp_path)
