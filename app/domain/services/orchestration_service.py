from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.schemas import EvaluationOut, GeneratedQuestion, SessionAnswerPayload
from app.domain.services.decision_service import DecisionService
from app.domain.services.diff_service import DiffService
from app.domain.services.evaluation_service import EvaluationService
from app.domain.services.policy_service import PolicyService
from app.domain.services.question_service import QuestionService
from app.domain.services.reporting_service import ReportingService
from app.integrations.github.client import GitHubClient
from app.integrations.github.reporter import GitHubReporter
from app.persistence import models


class OrchestrationService:
    def __init__(self, db: Session):
        self.db = db
        self.policy_service = PolicyService()
        self.diff_service = DiffService()
        self.question_service = QuestionService()
        self.evaluation_service = EvaluationService()
        self.decision_service = DecisionService()
        self.reporting_service = ReportingService()
        self.github_client = GitHubClient(settings.github_token)
        self.github_reporter = GitHubReporter(settings.github_token)

    def start_session(self, context) -> int:
        repo = self._get_or_create_repo(context.repo_id, context.repo_name)

        existing = self.db.execute(
            select(models.PullRequestSession).where(
                models.PullRequestSession.repository_id == repo.id,
                models.PullRequestSession.pr_number == context.pr_number,
                models.PullRequestSession.head_sha == context.head_sha,
            )
        ).scalar_one_or_none()
        if existing:
            return existing.id

        policy = self.policy_service.get_default_policy()

        changed_files = self.github_client.get_changed_files(context.repo_name, context.pr_number)
        normalized = self.diff_service.normalize(changed_files)

        session = models.PullRequestSession(
            repository_id=repo.id,
            provider="github",
            pr_number=context.pr_number,
            head_sha=context.head_sha,
            base_sha=context.base_sha,
            status="awaiting_answers",
            policy_id=policy.metadata.policy_id,
            policy_version=policy.metadata.version,
        )
        self.db.add(session)
        self.db.flush()

        diff = models.DiffArtifact(
            session_id=session.id,
            raw_diff="",
            normalized_diff=normalized.model_dump(),
            file_count=normalized.file_count,
            additions=normalized.additions,
            deletions=normalized.deletions,
            languages_detected=normalized.languages_detected,
        )
        self.db.add(diff)

        question_set = self.question_service.generate(policy, normalized.model_dump())
        qs = models.QuestionSet(
            session_id=session.id,
            generator_model=question_set.generator_model,
            policy_version=policy.metadata.version,
        )
        self.db.add(qs)
        self.db.flush()

        for idx, q in enumerate(question_set.questions):
            self.db.add(
                models.Question(
                    question_set_id=qs.id,
                    question_key=q.id,
                    type=q.type,
                    text=q.text,
                    expected_focus=q.expected_focus,
                    order_index=idx,
                )
            )

        self.db.commit()

        session_url = f"{settings.api_base_url}/sessions/{session.id}/ui"
        self.github_reporter.publish_pending(context.repo_name, context.head_sha, session_url)

        return session.id

    def submit_answers(self, session_id: int, payload: SessionAnswerPayload) -> dict:
        session = self.db.get(models.PullRequestSession, session_id)
        if not session:
            raise ValueError("Session not found")

        diff = self.db.execute(
            select(models.DiffArtifact).where(models.DiffArtifact.session_id == session.id)
        ).scalar_one()

        questions = self.db.execute(
            select(models.Question)
            .join(models.QuestionSet, models.Question.question_set_id == models.QuestionSet.id)
            .where(models.QuestionSet.session_id == session.id)
            .order_by(models.Question.order_index.asc())
        ).scalars().all()

        submission = models.AnswerSubmission(
            session_id=session.id,
            submitted_by=payload.submitted_by,
            raw_payload=payload.model_dump(),
        )
        self.db.add(submission)
        self.db.flush()

        policy = self.policy_service.get_default_policy()
        evaluations: list[EvaluationOut] = []

        for q in questions:
            answer_text = payload.answers.get(q.question_key, "")
            answer = models.Answer(submission_id=submission.id, question_id=q.id, answer_text=answer_text)
            self.db.add(answer)
            self.db.flush()

            q_schema = GeneratedQuestion(id=q.question_key, text=q.text, type=q.type, expected_focus=q.expected_focus)
            evaluation = self.evaluation_service.evaluate(
                policy=policy,
                question=q_schema,
                answer_text=answer_text,
                normalized_diff=diff.normalized_diff,
            )
            evaluations.append(evaluation)

            self.db.add(
                models.EvaluationResult(
                    answer_id=answer.id,
                    evaluator_model=settings.llm_model,
                    score=evaluation.score,
                    passed=evaluation.passed,
                    rationale_summary=evaluation.rationale_summary,
                    missing_points=evaluation.missing_points,
                    ideal_answer=evaluation.ideal_answer,
                )
            )

        passed, final_score, reason = self.decision_service.decide(evaluations, policy)
        reviewer_summary = self.reporting_service.build_reviewer_summary(passed, final_score)

        decision = models.GateDecision(
            session_id=session.id,
            final_score=final_score,
            passed=passed,
            decision_reason=reason,
            reviewer_summary=reviewer_summary,
        )
        self.db.add(decision)
        session.status = "passed" if passed else "failed"

        self.db.commit()

        repo = self.db.get(models.Repository, session.repository_id)
        comment = self.reporting_service.build_author_feedback(passed, evaluations)
        self.github_reporter.publish_final(
            repo_name=repo.name,
            pr_number=session.pr_number,
            head_sha=session.head_sha,
            passed=passed,
            summary=reviewer_summary,
            comment=comment,
        )

        return {
            "session_id": session.id,
            "passed": passed,
            "final_score": final_score,
            "decision_reason": reason,
            "reviewer_summary": reviewer_summary,
        }

    def _get_or_create_repo(self, external_repo_id: int, name: str) -> models.Repository:
        repo = self.db.execute(select(models.Repository).where(models.Repository.name == name)).scalar_one_or_none()
        if repo:
            return repo

        repo = models.Repository(
            provider="github",
            external_repo_id=str(external_repo_id),
            name=name,
        )
        self.db.add(repo)
        self.db.flush()
        return repo
