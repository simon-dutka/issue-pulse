from datetime import datetime


class GitHubError(Exception):
    pass


class GitHubNotFound(GitHubError):
    pass


class GitHubAPIError(GitHubError):
    pass


class RateLimitExceeded(GitHubError):
    def __init__(self, reset_at: datetime):
        self.reset_at = reset_at
        super().__init__(f"GitHub rate limit reached, resets at {reset_at}")
