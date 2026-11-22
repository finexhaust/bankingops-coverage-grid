import json
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).parents[2]


def test_profile_is_layered_and_contains_no_instances():
    profile = yaml.safe_load((ROOT / "specs/insight-construction-profile.yaml").read_text())
    meta = profile["profile"]
    assert meta["layered_on"] == "bocg-common-semantics"
    assert meta["scope"]["definitions_only"] is True
    assert meta["scope"]["occurrence_instances_permitted"] is False


def test_profile_contains_temporal_semantics_for_lifecycle_states():
    profile = yaml.safe_load((ROOT / "specs/insight-construction-profile.yaml").read_text())
    temporal = profile["lifecycle_vocabulary"]["temporal_semantics"]
    assert "occurred_at" in temporal
    assert temporal["occurred_at"]["source_anchor_required"] is True
    assert "deadline_ref" in temporal
    assert temporal["deadline_ref"]["citation_required"] is True
    assert "calendar_ref" in temporal


def test_revision_vocabularies_and_feasibility_outcomes_are_non_gating():
    profile = yaml.safe_load((ROOT / "specs/insight-construction-profile.yaml").read_text())
    rubric = yaml.safe_load((ROOT / "specs/rubrics/episode-feasibility.yaml").read_text())["rubric"]
    families = yaml.safe_load((ROOT / "specs/rubrics/five-families.yaml").read_text())["rubric"]
    assert profile["profile"]["version"] == "0.3.0"
    assert {"draft", "reviewed", "withdrawn"}.issubset(profile["composition_lifecycle"]["states"])
    assert "stale" in profile["composition_lifecycle"]["review_states"]
    assert rubric["classification_version"] == 2
    assert rubric["diagnostic_effect"] == "no_gate_no_deletion"
    assert "NULL" not in rubric["classification"]["classes"]
    assert rubric["classification"]["missing_outcome_valid"] is True
    assert rubric["classification"]["optional"] is True
    assert families["version"] == "1.1.0"
    assert {"INDETERMINATE", "UNCERTAIN"}.issubset(families["verdicts"])


def test_new_episode_terms_validate_and_author_completion_needs_weight(insight_validator):
    group = {
        "kind": "TraceHypothesisGroup",
        "group_id": "group-test",
        "trace_ids": ["trace-a", "trace-b"],
        "single_process_instance_asserted": False,
    }
    insight_validator.validate(group)

    episode = _episode_fixture(
        composition_status="reviewed",
        review_status="stale",
        review_history=[{
            "reviewer_role": "sme",
            "reviewed_at": "2026-01-01T00:00:00Z",
            "review_status": "stale",
        }],
        adjudications=[{
            "adjudicator_role": "author",
            "basis": "author_supplied_completion",
            "independent_provenance_weight": 0.8,
        }],
        open_questions=[{"question_type": "outcome", "question": "Is an outcome established?"}],
    )
    insight_validator.validate(episode)

    episode["adjudications"][0].pop("independent_provenance_weight")
    assert list(insight_validator.iter_errors(episode))


def test_rejection_is_reasoned_attributed_and_reopenable(insight_validator):
    episode = _episode_fixture(
        composition_status="rejected",
        rejection={"reason": "Insufficient support", "attributed_to": "sme", "reopenable": True},
    )
    insight_validator.validate(episode)
    episode["rejection"]["reopenable"] = False
    assert list(insight_validator.iter_errors(episode))


def test_atom_without_content_origin_does_not_require_provenance_weight(insight_validator):
    atom = {
        "kind": "ObservationAtom",
        "atom_id": "a-no-origin",
        "predicate": "generic_assertion",
        "assertion_status": "asserted",
        "source_refs": [{
            "source_id": "synthetic-source",
            "lines": [1, 1],
            "selected_content_sha256": "0" * 64,
        }],
    }
    insight_validator.validate(atom)


def test_indeterminate_scenario_ledger_verdict_validates():
    schema = json.loads((ROOT / "specs/scenario-run-ledger-rows.schema.json").read_text())
    ledger = json.loads((ROOT / "specs/scenario-run-ledger.example.json").read_text())
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    assert not list(validator.iter_errors(ledger))
    for row in ledger["rows"]:
        row["verdict"] = "INDETERMINATE"
    assert not list(validator.iter_errors(ledger))


def test_institutional_directive_keeps_execution_unobserved():
    schema = json.loads((ROOT / "specs/institutional-speech-act.schema.json").read_text())
    value = {
        "schema": "kg-institutional-speech-act-expansion.v1",
        "literal_speech_act": {"type": "confirmation_request"},
        "institutional_speech_act": {"type": "directive"},
        "pragmatic_expansion": {"expanded_reading": "Confirm the earliest feasible execution time and then execute.", "basis": ["managerial_authority"], "adjudication_status": "sme_confirmed"},
        "obligation_frame": {"directive_status": "directed", "execution_status": "not_observed", "completion_status": "not_observed", "verification_status": "not_observed"},
        "state_separation_enforced": True,
    }
    jsonschema.Draft202012Validator(schema).validate(value)
    value["obligation_frame"]["execution_status"] = "executed"
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(value))


@pytest.fixture
def insight_validator():
    schema = json.loads((ROOT / "specs/insight-construction.schema.json").read_text())
    return jsonschema.Draft202012Validator(schema)


def _episode_fixture(**status_overrides):
    return {
        "kind": "Episode",
        "episode_id": "ep-test-temporal",
        "atom_ids": ["a1"],
        "composition_status": "candidate",
        **status_overrides,
    }


def test_episode_accepts_plain_lifecycle_state(insight_validator):
    episode = _episode_fixture(
        execution_status="scheduled",
        completion_status="not_observed",
        verification_status="not_observed",
    )
    insight_validator.validate(episode)


def test_episode_accepts_state_transition_with_occurred_at(insight_validator):
    episode = _episode_fixture(
        execution_status={"state": "executed", "occurred_at": "2026-09-20T14:30:00Z"},
        completion_status="not_observed",
        verification_status="not_observed",
    )
    insight_validator.validate(episode)


def test_episode_accepts_state_transition_with_deadline_and_calendar(insight_validator):
    episode = _episode_fixture(
        execution_status={
            "state": "scheduled",
            "deadline_ref": {"expression": "T+1 business day", "citation": "EMIR Art. 4 (Regulation (EU) 648/2012)"},
            "calendar_ref": "TARGET2",
        },
        completion_status="not_observed",
        verification_status="not_observed",
    )
    insight_validator.validate(episode)


def test_episode_rejects_state_transition_missing_required_deadline_fields(insight_validator):
    episode = _episode_fixture(
        execution_status={"state": "scheduled", "deadline_ref": {"expression": "T+1 business day"}},
        completion_status="not_observed",
        verification_status="not_observed",
    )
    assert list(insight_validator.iter_errors(episode))


def test_release_manifest_contains_every_spec_05_artifact():
    from build_release_manifest import STATIC_ARTIFACTS
    required = {
        "specs/SPEC-05-insight-construction.md",
        "specs/insight-construction-profile.yaml",
        "specs/insight-construction.schema.json",
        "specs/institutional-speech-act.schema.json",
        "specs/rubrics/episode-feasibility.yaml",
        "specs/rubrics/five-families.yaml",
    }
    assert required.issubset(STATIC_ARTIFACTS)
