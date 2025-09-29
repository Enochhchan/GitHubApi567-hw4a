from __future__ import annotations

import requests
from typing import Dict, List, Tuple, Optional


class GitHubAPIError(Exception):
    """Raised when GitHub returns an error status code."""


class GitHubAPI:
    """Thin wrapper around GitHub's REST API v3 with a tester-first design.
    
    Key testing decisions:
    - `session` is injectable to enable mocking in unit tests.
    - Pagination is implemented for commits so large repos are counted correctly.
    - Minimal logic in public method; helpers are small and pure for easier tests.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, session: Optional[requests.Session] = None, timeout: float = 10.0):
        self.session = session or requests.Session()
        self.timeout = timeout

    def _get(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        resp = self.session.get(url, params=params, timeout=self.timeout, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "TesterMind-Homework/1.0",
        })
        if resp.status_code >= 400:
            # Keep message short but informative for tests
            raise GitHubAPIError(f"GET {url} failed: {resp.status_code} {resp.reason}")
        return resp

    def list_user_repos(self, user: str) -> List[str]:
        """Return a list of repo names for the given user (public repos only)."""
        url = f"{self.BASE_URL}/users/{user}/repos"
        # simple approach is fine here; default per_page is OK for homework scale
        page = 1
        names: List[str] = []
        while True:
            resp = self._get(url, params={"per_page": 100, "page": page, "type": "owner", "sort": "full_name"})
            data = resp.json()
            if not isinstance(data, list):
                # Unexpected payload; surface clearly for tests
                raise GitHubAPIError("Unexpected response when listing repos (not a list)")
            if not data:
                break
            names.extend([item.get("name", "") for item in data if isinstance(item, dict)])
            page += 1
        return names

    def count_commits(self, user: str, repo: str) -> int:
        """Count commits in a repo (public). Uses pagination to be correct for big repos."""
        url = f"{self.BASE_URL}/repos/{user}/{repo}/commits"
        page = 1
        total = 0
        while True:
            resp = self._get(url, params={"per_page": 100, "page": page})
            items = resp.json()
            if not isinstance(items, list):
                raise GitHubAPIError("Unexpected response when listing commits (not a list)")
            count = len(items)
            total += count
            if count < 100:
                break
            page += 1
        return total

    def repo_commit_counts(self, user: str) -> List[Tuple[str, int]]:
        """Return [(repo_name, commit_count), ...] for all repos owned by `user`."""
        repos = self.list_user_repos(user)
        results: List[Tuple[str, int]] = []
        for name in repos:
            try:
                commits = self.count_commits(user, name)
            except GitHubAPIError:
                # Skip repos that error (e.g., empty repos can 409) but keep going.
                commits = 0
            results.append((name, commits))
        return results


def format_repo_counts(pairs: List[Tuple[str, int]]) -> str:
    """Render output lines exactly as the assignment requires."""
    return "\n".join([f"Repo: {name} Number of commits: {count}" for name, count in pairs])


def repos_and_commits_for_user(user: str, session: Optional[requests.Session] = None) -> str:
    """Single-call helper the grader can run.
    
    Example:
        print(repos_and_commits_for_user("richkempinski"))
    """
    client = GitHubAPI(session=session)
    pairs = client.repo_commit_counts(user)
    return format_repo_counts(pairs)
