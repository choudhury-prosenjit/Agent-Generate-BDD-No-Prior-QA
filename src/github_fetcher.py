"""Fetches source code files from a GitHub repository."""

import logging
import re
import base64
from typing import Optional

import requests

LOGGER = logging.getLogger(__name__)

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
    ".rb", ".cs", ".cpp", ".c", ".h", ".php", ".swift", ".kt", ".rs",
}

SKIP_DIRS = {
    "node_modules", ".git", "vendor", "dist", "build",
    "__pycache__", ".venv", "venv", "env",
    "test", "tests", "spec", "specs", "__tests__",
    ".github", "docs", "examples",
}

MAX_FILES = 30
MAX_FILE_SIZE_BYTES = 200_000  # 200 KB per file
MAX_TOTAL_CHARS = 500_000      # 500 KB of text overall


def parse_github_url(url: str) -> tuple:
    """Parse a GitHub repository URL and return (owner, repo).

    Supports formats:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
    """
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)$", url)
    if not match:
        raise ValueError(
            f"Invalid GitHub repository URL: '{url}'. "
            "Expected format: https://github.com/owner/repository"
        )
    return match.group(1), match.group(2)


def _make_headers(github_token: Optional[str]) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    return headers


def _check_rate_limit(response: requests.Response) -> None:
    """Raise a descriptive error if GitHub API rate limit is exceeded."""
    if response.status_code == 403:
        remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
        if remaining == "0" or "rate limit" in response.text.lower():
            raise ValueError(
                "GitHub API rate limit exceeded. "
                "Add a GITHUB_TOKEN to your .env file to increase the limit."
            )
    if response.status_code == 401:
        raise ValueError(
            "GitHub API authentication failed. "
            "Check that your GITHUB_TOKEN is valid."
        )


def _list_repo_files(owner: str, repo: str, branch: str, github_token: Optional[str]) -> list:
    """Return a filtered list of {path, sha, size} dicts from the repo tree."""
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}"
        "?recursive=1"
    )
    response = requests.get(url, headers=_make_headers(github_token), timeout=30)
    if response.status_code == 404:
        raise ValueError(
            f"Repository or branch not found: {owner}/{repo} @ {branch}. "
            "Check the URL and branch name."
        )
    _check_rate_limit(response)
    response.raise_for_status()

    tree = response.json()
    if tree.get("truncated"):
        LOGGER.warning("GitHub tree response is truncated — only partial file list returned.")

    selected = []
    for item in tree.get("tree", []):
        if item["type"] != "blob":
            continue

        path = item["path"]
        parts = path.split("/")

        # Skip unwanted directories
        if any(part in SKIP_DIRS for part in parts[:-1]):
            continue

        # Skip files without a recognised source extension
        dot_pos = path.rfind(".")
        ext = path[dot_pos:] if dot_pos != -1 else ""
        if ext not in SOURCE_EXTENSIONS:
            continue

        # Skip oversized files
        if item.get("size", 0) > MAX_FILE_SIZE_BYTES:
            LOGGER.warning("Skipping oversized file: %s (%d bytes)", path, item.get("size", 0))
            continue

        selected.append({"path": path, "sha": item["sha"], "size": item.get("size", 0)})
        if len(selected) >= MAX_FILES:
            break

    return selected


def _get_file_content(owner: str, repo: str, path: str, branch: str, github_token: Optional[str]) -> str:
    """Return the decoded text content of a single file."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    response = requests.get(url, headers=_make_headers(github_token), timeout=30)
    _check_rate_limit(response)
    response.raise_for_status()
    data = response.json()

    # GitHub returns content as base64 with newlines; handle missing/empty content gracefully
    raw_content = data.get("content", "")
    if not raw_content:
        # Fallback: try download_url for files GitHub can't base64-encode inline
        download_url = data.get("download_url")
        if download_url:
            dl_response = requests.get(download_url, headers=_make_headers(github_token), timeout=30)
            dl_response.raise_for_status()
            return dl_response.text
        return ""

    raw = base64.b64decode(raw_content)
    return raw.decode("utf-8", errors="replace")


def fetch_repository_code(url: str, branch: str, github_token: Optional[str] = None) -> dict:
    """Fetch source code files from a GitHub repository.

    Parameters
    ----------
    url : str
        GitHub repository URL (e.g. https://github.com/owner/repo).
    branch : str
        Branch name (e.g. "main").
    github_token : str, optional
        Personal access token for higher rate limits or private repos.

    Returns
    -------
    dict
        Mapping of file path → file content (text).
    """
    owner, repo = parse_github_url(url)
    file_list = _list_repo_files(owner, repo, branch, github_token)

    if not file_list:
        # Give a helpful hint about size limit too
        raise ValueError(
            f"No supported source files found in '{owner}/{repo}' on branch '{branch}'. "
            f"Files must be ≤ {MAX_FILE_SIZE_BYTES // 1000} KB and use one of these extensions: "
            f"{', '.join(sorted(SOURCE_EXTENSIONS))}."
        )

    result = {}
    total_chars = 0
    fetch_errors = []

    for file_info in file_list:
        try:
            content = _get_file_content(owner, repo, file_info["path"], branch, github_token)
        except ValueError:
            # Re-raise auth / rate-limit errors immediately
            raise
        except Exception as exc:
            LOGGER.warning("Could not fetch %s: %s", file_info["path"], exc)
            fetch_errors.append(f"{file_info['path']}: {exc}")
            continue

        total_chars += len(content)
        if total_chars > MAX_TOTAL_CHARS:
            LOGGER.info("Total character limit reached — stopping early.")
            break

        result[file_info["path"]] = content

    if not result and fetch_errors:
        raise ValueError(
            f"Found {len(file_list)} source file(s) but could not fetch any content.\n"
            + "\n".join(fetch_errors)
        )

    return result
