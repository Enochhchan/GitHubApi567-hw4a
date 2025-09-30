import unittest
from unittest.mock import patch, Mock

from src.github_api import GitHubAPI, repos_and_commits_for_user, GitHubAPIError


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, reason="OK"):
        self.status_code = status_code
        self._json = json_data
        self.reason = reason
    def json(self):
        return self._json


class MockingTests(unittest.TestCase):
    @patch("requests.Session.get")
    def test_repo_commit_counts_happy_path(self, mock_get):
        """
        Simulates:
          - list repos (page1) -> two repos
          - list repos (page2) -> empty
          - commits for repoA (page1) -> 2
          - commits for repoA (page2) -> empty
          - commits for repoB (page1) -> 1
          - commits for repoB (page2) -> empty
        No real network calls.
        """
        mock_get.side_effect = [
            # list_user_repos pages
            FakeResponse(200, [{"name": "repoA"}, {"name": "repoB"}]),
            FakeResponse(200, []),

            # commits for repoA pages
            FakeResponse(200, [{}, {}]),
            FakeResponse(200, []),

            # commits for repoB pages
            FakeResponse(200, [{}]),
            FakeResponse(200, []),
        ]

        api = GitHubAPI()  # unchanged app code
        pairs = api.repo_commit_counts("someuser")
        self.assertEqual(pairs, [("repoA", 2), ("repoB", 1)])
        self.assertGreaterEqual(mock_get.call_count, 6)  # sanity: used the mock, not the network

    @patch("requests.Session.get")
    def test_error_repo_is_counted_zero_and_flow_continues(self, mock_get):
        """
        First repo ok, second repo errors on commits.
        App code catches GitHubAPIError and records 0 for that repo.
        """
        mock_get.side_effect = [
            # repos:
            FakeResponse(200, [{"name": "ok"}, {"name": "bad"}]),
            FakeResponse(200, []),

            # commits for ok (2 commits then end):
            FakeResponse(200, [{}, {}]),
            FakeResponse(200, []),

            # commits for bad -> _get should raise via status_code >= 400
            FakeResponse(500, {"message": "boom"}, reason="Server Error"),
        ]

        api = GitHubAPI()
        out = api.repo_commit_counts("user")
        self.assertEqual(out, [("ok", 2), ("bad", 0)])

    @patch("requests.Session.get")
    def test_top_level_helper_uses_mock_only(self, mock_get):
        """
        End-to-end via the convenience function, but fully mocked.
        """
        mock_get.side_effect = [
            # repos:
            FakeResponse(200, [{"name": "gamma"}]),
            FakeResponse(200, []),

            # commits for gamma:
            FakeResponse(200, [{}, {}, {}]),
            FakeResponse(200, []),
        ]

        text = repos_and_commits_for_user("someone")
        self.assertEqual(text, "Repo: gamma Number of commits: 3")

    @patch("requests.Session.get")
    def test_list_user_repos_raises_on_http_error(self, mock_get):
        mock_get.return_value = FakeResponse(404, {"message": "Not Found"}, reason="Not Found")
        api = GitHubAPI()
        with self.assertRaises(GitHubAPIError):
            api.list_user_repos("nope")


if __name__ == "__main__":
    unittest.main()
