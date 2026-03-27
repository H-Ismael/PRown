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

    def set_check_run(self, repo_name: str, head_sha: str, name: str, conclusion: str, summary: str) -> None:
        if not self.token:
            return
        url = f"{self.BASE_URL}/repos/{repo_name}/check-runs"
        payload = {
            "name": name,
            "head_sha": head_sha,
            "status": "completed",
            "conclusion": conclusion,
            "output": {"title": name, "summary": summary[:65000]},
        }
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()

    def create_pr_comment(self, repo_name: str, pr_number: int, body: str) -> None:
        if not self.token:
            return
        url = f"{self.BASE_URL}/repos/{repo_name}/issues/{pr_number}/comments"
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, headers=self._headers(), json={"body": body})
            resp.raise_for_status()
