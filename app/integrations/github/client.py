import httpx


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.token = token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_changed_files(self, repo_name: str, pr_number: int) -> list[dict]:
        if not self.token:
            return []
        url = f"{self.BASE_URL}/repos/{repo_name}/pulls/{pr_number}/files"
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    def set_commit_status(
        self,
        repo_name: str,
        head_sha: str,
        context: str,
        state: str,
        description: str,
        target_url: str | None = None,
    ) -> None:
        if not self.token:
            return
        url = f"{self.BASE_URL}/repos/{repo_name}/statuses/{head_sha}"
        payload = {
            "state": state,
            "context": context,
            "description": description[:140],
        }
        if target_url:
            payload["target_url"] = target_url
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()

    def set_check_run(self, repo_name: str, head_sha: str, name: str, conclusion: str, summary: str) -> None:
        # Backward-compatible adapter for callers using old check-run vocabulary.
        state_map = {
            "neutral": "pending",
            "success": "success",
            "failure": "failure",
            "cancelled": "error",
            "timed_out": "error",
            "action_required": "error",
        }
        state = state_map.get(conclusion, "error")
        self.set_commit_status(
            repo_name=repo_name,
            head_sha=head_sha,
            context=name,
            state=state,
            description=summary,
        )

    def create_pr_comment(self, repo_name: str, pr_number: int, body: str) -> None:
        if not self.token:
            return
        url = f"{self.BASE_URL}/repos/{repo_name}/issues/{pr_number}/comments"
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, headers=self._headers(), json={"body": body})
            resp.raise_for_status()
