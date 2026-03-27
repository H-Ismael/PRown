from app.domain.schemas import EvaluationOut, Policy


class DecisionService:
    def decide(self, evaluations: list[EvaluationOut], policy: Policy) -> tuple[bool, float, str]:
        if not evaluations:
            return False, 0.0, "No evaluations were produced."

        scores = [e.score for e in evaluations]
        average_score = sum(scores) / len(scores)

        all_minimum = all(s >= policy.grading.min_question_score for s in scores)
        passed = average_score >= policy.grading.pass_threshold and all_minimum

        if passed:
            reason = "Author demonstrated sufficient understanding of the submitted diff."
        else:
            reason = "Understanding threshold not met; merge should remain blocked until improved answers are provided."

        return passed, average_score, reason
