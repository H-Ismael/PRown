from pathlib import Path

import yaml

from app.core.config import settings
from app.domain.schemas import Policy


class PolicyService:
    def __init__(self, policy_dir: str | None = None):
        self.policy_dir = Path(policy_dir or settings.policy_dir)

    def get_default_policy(self) -> Policy:
        return self.load_policy("generic_v1.yaml")

    def list_policies(self) -> list[dict]:
        policies = []
        for path in sorted(self.policy_dir.glob("*.yaml")):
            policy = self.load_policy(path.name)
            policies.append(
                {
                    "policy_id": policy.metadata.policy_id,
                    "version": policy.metadata.version,
                    "name": policy.metadata.name,
                    "file": path.name,
                }
            )
        return policies

    def load_policy(self, filename: str) -> Policy:
        full_path = self.policy_dir / filename
        with full_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return Policy.model_validate(data)
