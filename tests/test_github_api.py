import unittest
from unittest.mock import Mock
import requests

from src.github_api import GitHubAPI, format_repo_counts, repos_and_commits_for_user, GitHubAPIError


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, reason="OK"):
        self.status_code = status_code
        self._json = json_data
        self.reason = reason

    def json(self):
        return self._json


class FakeSession:
    """A tiny fake requests.Session that returns queued responses (no real HTTP)."""
    def __init__(self, responses):
        self._responses = responses[:]  # queue

    def get(self, url, params=None, timeout=None, headers=None):
        if not self._responses:
            raise AssertionError("No more fake responses queued for GET " + url)
        return self._responses.pop(0)


class TestGitHubAPI(unittest.TestCase):
    def test_list_user_repos_paginates(self):
        # page 1: two repos; page 2: empty
        session = FakeSession([
            FakeResponse(200, [{"name": "alpha"}, {"name": "beta"}]),
            FakeResponse(200, []),
        ])
        api = GitHubAPI(session=session)
        self.assertEqual(api.list_user_repos("someone"), ["alpha", "beta"])

    def test_count_commits_paginates(self):
        # simulate 101 commits -> 2 pages: first 100, then 1
        session = FakeSession([
            FakeResponse(200, [{}] * 100),
            FakeResponse(200, [{}]),
        ])
        api = GitHubAPI(session=session)
        self.assertEqual(api.count_commits("u", "r"), 101)

    def test_error_bubbles_up(self):
        session = FakeSession([FakeResponse(404, {"message": "Not Found"}, reason="Not Found")])
        api = GitHubAPI(session=session)
        with self.assertRaises(GitHubAPIError):
            api.list_user_repos("nope")  # triggers _get error

    def test_repo_commit_counts_skips_error_repo(self):
        # repos: [ok, bad]
        session = FakeSession([
            FakeResponse(200, [{"name": "ok"}, {"name": "bad"}]),  # list repos
            FakeResponse(200, [{}] * 2),   # commits for ok
            FakeResponse(500, {"message": "boom"}, reason="Server Error"),  # commits for bad
        ])
        api = GitHubAPI(session=session)
        out = api.repo_commit_counts("u")
        self.assertEqual(out, [("ok", 2), ("bad", 0)])  # bad repo counted as 0 but flow continues

    def test_format_matches_assignment(self):
        text = format_repo_counts([("Triangle567", 10), ("Square567", 27)])
        self.assertEqual(text, "Repo: Triangle567 Number of commits: 10\nRepo: Square567 Number of commits: 27")


class TestTopLevelHelper(unittest.TestCase):
    def test_repos_and_commits_for_user_uses_client(self):
        # repos: gamma; commits: 3
        session = FakeSession([
            FakeResponse(200, [{"name": "gamma"}]),
            FakeResponse(200, [{}] * 3),
            FakeResponse(200, []),
        ])
        text = repos_and_commits_for_user("someone", session=session)
        self.assertEqual(text, "Repo: gamma Number of commits: 3")


if __name__ == "__main__":
    unittest.main()
