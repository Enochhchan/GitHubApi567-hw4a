import types
import pytest
from unittest.mock import patch

from github_api import GitHubAPI, GitHubAPIError   # adjust if needed


def _resp_with_json(obj):
    """Tiny helper to mimic requests.Response with a json() method."""
    r = types.SimpleNamespace()
    r.json = lambda: obj
    return r


@patch.object(GitHubAPI, "_get")
def test_list_user_repos_raises_when_json_not_list(mock_get):
    """Covers: raise GitHubAPIError(...) in list_user_repos when JSON isn't a list."""
    mock_get.return_value = _resp_with_json({"message": "not-a-list"})
    api = GitHubAPI()
    with pytest.raises(GitHubAPIError):
        api.list_user_repos("octocat")


@patch.object(GitHubAPI, "_get")
def test_count_commits_raises_when_json_not_list(mock_get):
    """Covers: raise GitHubAPIError(...) in count_commits when JSON isn't a list."""
    mock_get.return_value = _resp_with_json({"message": "not-a-list"})
    api = GitHubAPI()
    with pytest.raises(GitHubAPIError):
        api.count_commits("octocat", "hello-world")


@patch.object(GitHubAPI, "_get")
def test_list_user_repos_pagination_empty_page_breaks(mock_get):
    """
    Covers the 'if not data: break' pagination branch:
    first page has 1 repo; second page empty -> loop breaks cleanly.
    """
    page1 = _resp_with_json([{"name": "r1"}])
    page2 = _resp_with_json([])  # triggers the break
    mock_get.side_effect = [page1, page2]

    api = GitHubAPI()
    names = api.list_user_repos("octocat")

    assert names == ["r1"]
    assert mock_get.call_count == 2  # we fetched page 1 then the empty page

from github_api import GitHubAPI, GitHubAPIError

@patch.object(GitHubAPI, "count_commits")
@patch.object(GitHubAPI, "list_user_repos")
def test_repo_commit_counts_skips_errors(mock_list, mock_count):
    mock_list.return_value = ["repo1"]
    mock_count.side_effect = GitHubAPIError("bad repo")

    api = GitHubAPI()
    result = api.repo_commit_counts("octocat")

    # Should append ("repo1", 0) instead of crashing
    assert result == [("repo1", 0)]

    from github_api import format_repo_counts

def test_format_repo_counts_output():
    pairs = [("r1", 5), ("r2", 0)]
    out = format_repo_counts(pairs)
    assert "Repo: r1 Number of commits: 5" in out
    assert "Repo: r2 Number of commits: 0" in out

from github_api import repos_and_commits_for_user

def test_repos_and_commits_for_user(monkeypatch):
    # Patch the GitHubAPI methods used inside
    import github_api
    monkeypatch.setattr(github_api.GitHubAPI, "repo_commit_counts",
                        lambda self, user: [("demo", 3)])

    out = repos_and_commits_for_user("octocat")
    assert "Repo: demo Number of commits: 3" in out
