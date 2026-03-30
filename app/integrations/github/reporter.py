import logging

from app.integrations.github.client import GitHubClient

logger = logging.getLogger(__name__)


class GitHubReporter:
    def __init__(self, token: str):
        self.client = GitHubClient(token)

    def publish_pending(self, repo_name: str, head_sha: str, session_url: str):
        summary = (
            "Comprehension assessment started. "
            f"Author must answer questions at: {session_url}"
        )
        try:
            self.client.set_commit_status(
                repo_name=repo_name,
                head_sha=head_sha,
                context="pr-comprehension-gate",
                state="pending",
                description=summary,
                target_url=session_url,
            )
        except Exception:
            logger.exception("Failed to publish pending commit status for %s@%s", repo_name, head_sha)

    def publish_final(
        self,
        repo_name: str,
        pr_number: int,
        head_sha: str,
        passed: bool,
        summary: str,
        comment: str,
    ):
        state = "success" if passed else "failure"
        try:
            self.client.set_commit_status(
                repo_name=repo_name,
                head_sha=head_sha,
                context="pr-comprehension-gate",
                state=state,
                description=summary,
            )
        except Exception:
            logger.exception("Failed to publish final commit status for %s@%s", repo_name, head_sha)

        try:
            self.client.create_pr_comment(repo_name=repo_name, pr_number=pr_number, body=comment)
        except Exception:
            logger.exception("Failed to publish PR comment for %s#%s", repo_name, pr_number)
