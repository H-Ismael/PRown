from app.domain.schemas import (
    EvaluationOut,
    Policy,
)
from app.domain.services.decision_service import DecisionService


def sample_policy() -> Policy:
    return Policy.model_validate(
        {
            "metadata": {"policy_id": "generic_v1", "version": 1, "name": "Generic"},
            "selection": {"include_paths": [], "exclude_paths": [], "min_changed_lines": 0},
            "questioning": {"max_questions": 2, "types": [], "constraints": []},
            "grading": {
                "pass_threshold": 0.75,
                "min_question_score": 0.5,
                "allow_partial_credit": True,
                "require_behavioral_grounding": True,
            },
            "feedback": {
                "reveal_ideal_answer": True,
                "constructive_mode": True,
                "generate_reviewer_summary": True,
            },
        }
    )


def test_decision_passes_when_thresholds_met():
    svc = DecisionService()
    policy = sample_policy()
    evaluations = [
        EvaluationOut(score=0.9, passed=True, rationale_summary="", missing_points=[], ideal_answer=""),
        EvaluationOut(score=0.8, passed=True, rationale_summary="", missing_points=[], ideal_answer=""),
    ]

    passed, score, _ = svc.decide(evaluations, policy)

    assert passed is True
    assert score == 0.85


def test_decision_fails_when_one_answer_below_minimum():
    svc = DecisionService()
    policy = sample_policy()
    evaluations = [
        EvaluationOut(score=0.95, passed=True, rationale_summary="", missing_points=[], ideal_answer=""),
        EvaluationOut(score=0.49, passed=False, rationale_summary="", missing_points=[], ideal_answer=""),
    ]

    passed, score, _ = svc.decide(evaluations, policy)

    assert passed is False
    assert score == 0.72
