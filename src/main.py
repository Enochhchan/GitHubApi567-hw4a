from src.github_api import repos_and_commits_for_user

def main() -> None:
    user = input("Enter a GitHub user ID: ").strip()
    print(repos_and_commits_for_user(user))

if __name__ == "__main__":
    main()
