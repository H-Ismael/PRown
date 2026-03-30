from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_github_signature
from app.domain.services.orchestration_service import OrchestrationService
from app.integrations.github.mapper import GitHubMapper
from app.persistence.db import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    body = await request.body()
    if not verify_github_signature(settings.github_webhook_secret, body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()

    if x_github_event != "pull_request":
        return {"accepted": True, "message": "ignored event"}

    action = payload.get("action")
    if action not in {"opened", "synchronize", "reopened"}:
        return {"accepted": True, "message": f"ignored action {action}"}

    mapper = GitHubMapper()
    context = mapper.to_pr_context(payload)

    orchestrator = OrchestrationService(db)
    session_id = orchestrator.start_session(context)

    return {"accepted": True, "session_id": session_id}
