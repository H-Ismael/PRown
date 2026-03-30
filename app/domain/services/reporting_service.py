from app.domain.schemas import EvaluationOut


class ReportingService:
    def build_author_feedback(self, passed: bool, evaluations: list[EvaluationOut]) -> str:
        lines = ["## PR Comprehension Gate Result", ""]
        lines.append(f"- Result: {'PASS' if passed else 'FAIL'}")
        lines.append("")
        for idx, ev in enumerate(evaluations, start=1):
            lines.append(f"### Question {idx}")
            lines.append(f"- Score: {ev.score:.2f}")
            lines.append(f"- Passed: {'yes' if ev.passed else 'no'}")
            lines.append(f"- Missing Points: {', '.join(ev.missing_points) if ev.missing_points else 'none'}")
            lines.append(f"- Rationale: {ev.rationale_summary}")
            lines.append(f"- Ideal Answer: {ev.ideal_answer}")
            lines.append("")
        return "\n".join(lines)

    def build_reviewer_summary(self, passed: bool, score: float) -> str:
        return (
            f"Comprehension gate {'passed' if passed else 'failed'} "
            f"with final score {score:.2f}."
        )
