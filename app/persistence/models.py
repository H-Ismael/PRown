from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.db import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(Text, default="github")
    external_repo_id: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text, unique=True)
    default_branch: Mapped[str] = mapped_column(Text, default="main")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PullRequestSession(Base):
    __tablename__ = "pull_request_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    provider: Mapped[str] = mapped_column(Text, default="github")
    pr_number: Mapped[int] = mapped_column(Integer)
    head_sha: Mapped[str] = mapped_column(Text)
    base_sha: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="awaiting_answers")
    policy_id: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repository: Mapped[Repository] = relationship()


class DiffArtifact(Base):
    __tablename__ = "diff_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("pull_request_sessions.id"), unique=True)
    raw_diff: Mapped[str] = mapped_column(Text)
    normalized_diff: Mapped[dict] = mapped_column(JSONB)
    file_count: Mapped[int] = mapped_column(Integer)
    additions: Mapped[int] = mapped_column(Integer)
    deletions: Mapped[int] = mapped_column(Integer)
    languages_detected: Mapped[list] = mapped_column(JSONB)


class QuestionSet(Base):
    __tablename__ = "question_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("pull_request_sessions.id"), unique=True)
    generator_model: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[int] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_set_id: Mapped[int] = mapped_column(ForeignKey("question_sets.id"))
    question_key: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    expected_focus: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)


class AnswerSubmission(Base):
    __tablename__ = "answer_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("pull_request_sessions.id"))
    submitted_by: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    raw_payload: Mapped[dict] = mapped_column(JSONB)


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("answer_submissions.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    answer_text: Mapped[str] = mapped_column(Text)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.id"))
    evaluator_model: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    rationale_summary: Mapped[str] = mapped_column(Text)
    missing_points: Mapped[list] = mapped_column(JSONB)
    ideal_answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GateDecision(Base):
    __tablename__ = "gate_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("pull_request_sessions.id"), unique=True)
    final_score: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    decision_reason: Mapped[str] = mapped_column(Text)
    reviewer_summary: Mapped[str] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
