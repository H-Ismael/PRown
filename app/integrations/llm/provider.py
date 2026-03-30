import json

from app.core.config import settings
from app.domain.schemas import EvaluationOut, GeneratedQuestion, Policy


class LLMProvider:
    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.api_base = settings.llm_api_base

    def generate_questions(self, policy: Policy, diff_summary: dict) -> list[GeneratedQuestion]:
        if self.provider == "litellm" and self.model:
            return self._generate_questions_litellm(policy, diff_summary)
        return self._generate_questions_stub(policy, diff_summary)

    def evaluate_answer(
        self,
        policy: Policy,
        question: GeneratedQuestion,
        answer: str,
        diff_summary: dict,
    ) -> EvaluationOut:
        if self.provider == "litellm" and self.model:
            return self._evaluate_answer_litellm(policy, question, answer, diff_summary)
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

    def _generate_questions_litellm(self, policy: Policy, diff_summary: dict) -> list[GeneratedQuestion]:
        prompt = {
            "policy": policy.model_dump(),
            "diff_summary": diff_summary,
            "instructions": "Return JSON list with id,text,type,expected_focus. Max 2 questions.",
        }
        text = self._litellm_text_response(json.dumps(prompt), temperature=0.2)
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("LLM questions output must be a JSON list")
        normalized = [self._normalize_generated_question(x, idx) for idx, x in enumerate(parsed, start=1)]
        return [GeneratedQuestion.model_validate(x) for x in normalized]

    def _evaluate_answer_litellm(
        self,
        policy: Policy,
        question: GeneratedQuestion,
        answer: str,
        diff_summary: dict,
    ) -> EvaluationOut:
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
        text = self._litellm_text_response(json.dumps(payload), temperature=0)
        data = json.loads(text)
        return EvaluationOut.model_validate(data)

    def _litellm_text_response(self, prompt: str, temperature: float) -> str:
        from litellm import completion

        completion_response = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            api_key=self.api_key or None,
            api_base=self.api_base or None,
        )
        content = completion_response.choices[0].message.content or ""
        return self._strip_markdown_fences(content).strip()

    @staticmethod
    def _normalize_generated_question(raw: dict, index: int) -> dict:
        if not isinstance(raw, dict):
            return {
                "id": f"q{index}",
                "text": str(raw),
                "type": "behavior_change",
                "expected_focus": "Explain runtime behavior and affected paths.",
            }

        question_id = raw.get("id", f"q{index}")
        text = raw.get("text", "")
        qtype = raw.get("type", "behavior_change")
        expected_focus = raw.get("expected_focus", "Explain runtime behavior and affected paths.")

        return {
            "id": str(question_id),
            "text": str(text),
            "type": str(qtype),
            "expected_focus": str(expected_focus),
        }

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3:
                return "\n".join(lines[1:-1])
        return text
