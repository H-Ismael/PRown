from typing import Any

from pydantic import BaseModel, Field


class PolicyMetadata(BaseModel):
    policy_id: str
    version: int
    name: str


class PolicySelection(BaseModel):
    include_paths: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)
    min_changed_lines: int = 0


class PolicyQuestioning(BaseModel):
    max_questions: int = 2
    types: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class PolicyGrading(BaseModel):
    pass_threshold: float = 0.75
    min_question_score: float = 0.5
    allow_partial_credit: bool = True
    require_behavioral_grounding: bool = True


class PolicyFeedback(BaseModel):
    reveal_ideal_answer: bool = True
    constructive_mode: bool = True
    generate_reviewer_summary: bool = True


class Policy(BaseModel):
    metadata: PolicyMetadata
    selection: PolicySelection
    questioning: PolicyQuestioning
    grading: PolicyGrading
    feedback: PolicyFeedback


class NormalizedDiff(BaseModel):
    files: list[dict[str, Any]]
    file_count: int
    additions: int
    deletions: int
    languages_detected: list[str]


class GeneratedQuestion(BaseModel):
    id: str
    text: str
    type: str
    expected_focus: str


class QuestionSetOut(BaseModel):
    questions: list[GeneratedQuestion]
    generator_model: str


class EvaluationOut(BaseModel):
    score: float
    passed: bool
    rationale_summary: str
    missing_points: list[str]
    ideal_answer: str


class SessionAnswerPayload(BaseModel):
    submitted_by: str = "author"
    answers: dict[str, str]


class SessionResultOut(BaseModel):
    session_id: int
    passed: bool
    final_score: float
    decision_reason: str
    reviewer_summary: str


class GitHubPRContext(BaseModel):
    repo_name: str
    repo_id: int
    pr_number: int
    head_sha: str
    base_sha: str
    installation_id: int | None = None
    pull_request_url: str
    changed_files: list[dict[str, Any]] = Field(default_factory=list)
