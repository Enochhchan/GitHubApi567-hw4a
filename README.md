# GitHubApi567-hw4a

A tiny, tester-minded Python 3 app that prints each repo for a GitHub user with its commit count.

## Usage

```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
# Enter: richkempinski
```

## Run tests

```bash
python -m unittest -v
```

## Design notes (tester perspective)

- **Injectable session**: `GitHubAPI` accepts a `requests.Session`, enabling fast unit tests with a fake session (no real HTTP).
- **Pagination**: Commits are paginated so big repos count correctly (common student pitfall).
- **Small helpers**: Methods do one thing → easier to unit test.
- **Resilience**: If one repo errors (e.g., empty repo `409`), it is counted as 0 and the program continues—observable behavior is testable.

### Rate limits

Unauthenticated rate limit is small. Our unit tests **never** hit GitHub; they use a fake session. For manual runs, if you hit rate limits, wait a bit or add a token to your environment and use it in the `Session` headers.

## CI

### Travis CI

Add your repo in Travis, then keep this `.travis.yml` in the root.
The badge (replace `USER/REPO`):
```
[![Build Status](https://travis-ci.com/USER/REPO.svg?branch=main)](https://travis-ci.com/USER/REPO)
```

### CircleCI

Enable your repo in CircleCI. This project includes `.circleci/config.yml`.

---

For graders: single-call entry point is `repos_and_commits_for_user(<user>)`.
