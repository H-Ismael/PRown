from app.domain.schemas import EvaluationOut, GeneratedQuestion, Policy
from app.integrations.llm.provider import LLMProvider


class EvaluationService:
    def __init__(self):
        self.llm = LLMProvider()

    def evaluate(
        self,
        policy: Policy,
        question: GeneratedQuestion,
        answer_text: str,
        normalized_diff: dict,
    ) -> EvaluationOut:
        return self.llm.evaluate_answer(policy, question, answer_text, normalized_diff)
