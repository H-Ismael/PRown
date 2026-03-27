import json

from app.core.config import settings
from app.domain.schemas import EvaluationOut, GeneratedQuestion, Policy


class LLMProvider:
    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model

    def generate_questions(self, policy: Policy, diff_summary: dict) -> list[GeneratedQuestion]:
        if self.provider == "openai" and settings.openai_api_key:
            return self._generate_questions_openai(policy, diff_summary)
        return self._generate_questions_stub(policy, diff_summary)

    def evaluate_answer(
        self,
        policy: Policy,
        question: GeneratedQuestion,
        answer: str,
        diff_summary: dict,
    ) -> EvaluationOut:
        if self.provider == "openai" and settings.openai_api_key:
            return self._evaluate_answer_openai(policy, question, answer, diff_summary)
        return self._evaluate_answer_stub(policy, question, answer)

    def _generate_questions_stub(self, policy: Policy, diff_summary: dict) -> list[GeneratedQuestion]:
        files = [f.get("filename", "unknown") for f in diff_summary.get("files", [])[:2]]
        file_hint = ", ".join(files) if files else "the changed files"
        max_q = max(1, min(policy.questioning.max_questions, 2))

        bank = [
            GeneratedQuestion(
                id="q1",
                text=f"What behavior change does this PR introduce in {file_hint}?",
                type="behavior_change",
                expected_focus="Explain runtime behavior and affected paths.",
            ),
            GeneratedQuestion(
                id="q2",
                text="What risk did you consider in this diff and how did you mitigate it?",
                type="risk_identification",
                expected_focus="Show specific risk and mitigation grounded in code changes.",
            ),
        ]
        return bank[:max_q]

    def _evaluate_answer_stub(self, policy: Policy, question: GeneratedQuestion, answer: str) -> EvaluationOut:
        tokens = set(answer.lower().split())
        score = 0.15
        expected_keywords = {
            "behavior_change": {"change", "because", "path", "function", "result"},
            "risk_identification": {"risk", "mitigate", "edge", "failure", "test"},
            "invariant_preservation": {"invariant", "preserve", "before", "after"},
        }
        matches = sum(1 for k in expected_keywords.get(question.type, set()) if k in tokens)
        score += min(matches * 0.15, 0.75)

        if len(answer.strip()) > 220:
            score += 0.1
        score = min(score, 1.0)
        passed = score >= policy.grading.min_question_score

        missing = []
        if "because" not in tokens:
            missing.append("Explain causality from code to behavior.")
        if len(answer.strip()) < 80:
            missing.append("Answer is too brief and not diff-grounded.")

        ideal = (
            "A strong answer should reference exact changed behavior, affected files/functions, "
            "risk analysis, and why the implementation preserves expected invariants."
        )

        return EvaluationOut(
            score=score,
            passed=passed,
            rationale_summary="Stub evaluator scored based on diff-grounded specificity and completeness.",
            missing_points=missing,
            ideal_answer=ideal,
        )

    def _generate_questions_openai(self, policy: Policy, diff_summary: dict) -> list[GeneratedQuestion]:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = {
            "policy": policy.model_dump(),
            "diff_summary": diff_summary,
            "instructions": "Return JSON list with id,text,type,expected_focus. Max 2 questions.",
        }
        response = client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": json.dumps(prompt)}],
            temperature=0.2,
        )
        text = response.output_text
        parsed = json.loads(text)
        return [GeneratedQuestion.model_validate(x) for x in parsed]

    def _evaluate_answer_openai(
        self,
        policy: Policy,
        question: GeneratedQuestion,
        answer: str,
        diff_summary: dict,
    ) -> EvaluationOut:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        payload = {
            "policy": policy.model_dump(),
            "question": question.model_dump(),
            "answer": answer,
            "diff_summary": diff_summary,
            "instructions": (
                "Return strict JSON object with keys: score (0..1), passed (bool), rationale_summary, "
                "missing_points (list), ideal_answer. Use rubric-based grading."
            ),
        }
        response = client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": json.dumps(payload)}],
            temperature=0,
        )
        data = json.loads(response.output_text)
        return EvaluationOut.model_validate(data)
