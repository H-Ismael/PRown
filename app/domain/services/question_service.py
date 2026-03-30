from app.domain.schemas import Policy, QuestionSetOut
from app.integrations.llm.provider import LLMProvider


class QuestionService:
    def __init__(self):
        self.llm = LLMProvider()

    def generate(self, policy: Policy, normalized_diff: dict) -> QuestionSetOut:
        questions = self.llm.generate_questions(policy, normalized_diff)
        return QuestionSetOut(questions=questions, generator_model=self.llm.model)
