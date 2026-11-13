from datetime import datetime

from pydantic import BaseModel, field_validator


class GitHubUser(BaseModel):
    type: str


class GitHubLabel(BaseModel):
    name: str


class GitHubIssue(BaseModel):
    id: int
    number: int
    title: str
    state: str
    comments: int
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    html_url: str
    author_association: str
    state_reason: str | None
    user: GitHubUser
    labels: list[GitHubLabel]
    assignee: bool
    pull_request: dict | None = None

    @field_validator("assignee", mode="before")
    @classmethod
    def assignee_to_bool(cls, value):
        return value is not None


class GitHubComment(BaseModel):
    id: int
    issue_url: str
    created_at: datetime
    author_association: str
    user: GitHubUser

    @property
    def issue_number(self) -> int:
        number_text = self.issue_url.rsplit("/", 1)[-1]
        return int(number_text)


class GitHubLicense(BaseModel):
    spdx_id: str | None


class GitHubRepository(BaseModel):
    id: int
    full_name: str
    html_url: str
    language: str | None
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    pushed_at: datetime
    created_at: datetime
    archived: bool
    has_issues: bool
    license: GitHubLicense | None = None
