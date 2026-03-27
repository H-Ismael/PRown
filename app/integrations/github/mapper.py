from app.domain.schemas import GitHubPRContext


class GitHubMapper:
    def to_pr_context(self, payload: dict) -> GitHubPRContext:
        pr = payload["pull_request"]
        repo = payload["repository"]

        return GitHubPRContext(
            repo_name=repo["full_name"],
            repo_id=repo["id"],
            pr_number=pr["number"],
            head_sha=pr["head"]["sha"],
            base_sha=pr["base"]["sha"],
            installation_id=(payload.get("installation") or {}).get("id"),
            pull_request_url=pr["url"],
        )
