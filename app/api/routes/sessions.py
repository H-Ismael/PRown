from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.schemas import SessionAnswerPayload
from app.domain.services.orchestration_service import OrchestrationService
from app.persistence import models
from app.persistence.db import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.get(models.PullRequestSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    questions = (
        db.execute(
            select(models.Question)
            .join(models.QuestionSet, models.Question.question_set_id == models.QuestionSet.id)
            .where(models.QuestionSet.session_id == session_id)
            .order_by(models.Question.order_index.asc())
        )
        .scalars()
        .all()
    )

    return {
        "id": session.id,
        "status": session.status,
        "questions": [
            {
                "id": q.id,
                "question_key": q.question_key,
                "text": q.text,
                "type": q.type,
                "expected_focus": q.expected_focus,
            }
            for q in questions
        ],
    }


@router.get("/{session_id}/ui")
def session_ui(request: Request, session_id: int, db: Session = Depends(get_db)):
    session_data = get_session(session_id, db)
    decision = db.execute(select(models.GateDecision).where(models.GateDecision.session_id == session_id)).scalar_one_or_none()

    return templates.TemplateResponse(
        "session.html",
        {
            "request": request,
            "session": session_data,
            "decision": decision,
        },
    )


@router.post("/{session_id}/answers")
def submit_answers(session_id: int, payload: SessionAnswerPayload, db: Session = Depends(get_db)):
    orchestrator = OrchestrationService(db)
    try:
        return orchestrator.submit_answers(session_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/ui")
async def submit_answers_ui(
    request: Request,
    session_id: int,
    submitted_by: str = Form(default="author"),
    db: Session = Depends(get_db),
):
    form = await request.form()
    answers = {}
    for key, value in form.items():
        if key.startswith("answer_"):
            question_key = key.replace("answer_", "")
            answers[question_key] = value

    payload = SessionAnswerPayload(submitted_by=submitted_by, answers=answers)
    orchestrator = OrchestrationService(db)
    orchestrator.submit_answers(session_id, payload)
    return RedirectResponse(url=f"/sessions/{session_id}/ui", status_code=303)


@router.get("/{session_id}/result")
def result(session_id: int, db: Session = Depends(get_db)):
    decision = db.execute(select(models.GateDecision).where(models.GateDecision.session_id == session_id)).scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="result not available yet")

    return {
        "session_id": session_id,
        "passed": decision.passed,
        "final_score": decision.final_score,
        "decision_reason": decision.decision_reason,
        "reviewer_summary": decision.reviewer_summary,
    }
