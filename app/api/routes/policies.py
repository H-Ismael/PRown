from fastapi import APIRouter

from app.domain.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("")
def list_policies():
    svc = PolicyService()
    return svc.list_policies()
