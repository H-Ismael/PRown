from app.integrations.github.client import GitHubClient


class GitHubReporter:
    def __init__(self, token: str):
        self.client = GitHubClient(token)

    def publish_pending(self, repo_name: str, head_sha: str, session_url: str):
        summary = (
            "Comprehension assessment started. "
            f"Author must answer questions at: {session_url}"
        )
        self.client.set_check_run(
            repo_name=repo_name,
            head_sha=head_sha,
            name="pr-comprehension-gate",
            conclusion="neutral",
            summary=summary,
        )

    def publish_final(
        self,
        repo_name: str,
        pr_number: int,
        head_sha: str,
        passed: bool,
        summary: str,
        comment: str,
    ):
        conclusion = "success" if passed else "failure"
        self.client.set_check_run(
            repo_name=repo_name,
            head_sha=head_sha,
            name="pr-comprehension-gate",
            conclusion=conclusion,
            summary=summary,
        )
        self.client.create_pr_comment(repo_name=repo_name, pr_number=pr_number, body=comment)
