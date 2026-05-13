import logging
import shutil
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class CloneError(RuntimeError):
    """Raised when repository clone fails."""


def clone_repository(repo_url: str, branch: str, destination: Path) -> Path:
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Cloning repository branch '%s' from %s", branch, repo_url)
    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--branch",
        branch,
        repo_url,
        str(destination),
    ]

    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode != 0:
        stderr = process.stderr.strip() or "Unknown clone error"
        raise CloneError(f"Failed to clone repository: {stderr}")

    return destination
