import argparse
import re
from pathlib import Path


_GITHUB_REPO_PATTERN = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+(?:\.git)?/?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a GitHub repository and generate BDD feature files."
    )
    parser.add_argument("--repo-url", required=True, help="GitHub repository URL")
    parser.add_argument("--branch", required=True, help="Branch name to analyze")
    parser.add_argument(
        "--output",
        default="./generated-features",
        help="Optional output folder path for generated .feature files",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="OpenAI model for code understanding and BDD generation",
    )
    return parser.parse_args()


def validate_repo_url(repo_url: str) -> None:
    if not _GITHUB_REPO_PATTERN.match(repo_url):
        raise ValueError(f"Invalid GitHub URL: {repo_url}")


def resolve_output_path(output_path: str) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path
