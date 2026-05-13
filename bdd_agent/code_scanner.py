import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

from .file_filter import FileFilter

LOGGER = logging.getLogger(__name__)


@dataclass
class ScannedFile:
    path: Path
    relative_path: str
    content: str


class CodeScanner:
    def __init__(self, file_filter: FileFilter | None = None) -> None:
        self.file_filter = file_filter or FileFilter()

    def scan(self, repo_root: Path) -> List[ScannedFile]:
        scanned: List[ScannedFile] = []
        for file_path in repo_root.rglob("*"):
            if not file_path.is_file():
                continue
            if self.file_filter.should_exclude_path(file_path.relative_to(repo_root)):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError as exc:
                LOGGER.warning("Skipping unreadable file %s: %s", file_path, exc)
                continue
            scanned.append(
                ScannedFile(
                    path=file_path,
                    relative_path=file_path.relative_to(repo_root).as_posix(),
                    content=content,
                )
            )

        if not scanned:
            raise ValueError("Unsupported repository structure: no analyzable source files found")

        LOGGER.info("Scanned %d analyzable files", len(scanned))
        return scanned

    def detect_frameworks(self, files: List[ScannedFile]) -> List[str]:
        frameworks: Set[str] = set()
        for file in files:
            name = file.relative_path.lower()
            content = file.content.lower()

            if name.endswith("package.json"):
                if "react" in content:
                    frameworks.add("React")
                if "@angular/core" in content:
                    frameworks.add("Angular")
                if "express" in content:
                    frameworks.add("Node.js")
            if name.endswith("pom.xml") and "spring-boot" in content:
                frameworks.add("Java Spring Boot")
            if name.endswith("build.gradle") and "spring-boot" in content:
                frameworks.add("Java Spring Boot")
            if name.endswith("requirements.txt") or name.endswith("pyproject.toml"):
                frameworks.add("Python")
            if name.endswith(".csproj"):
                frameworks.add(".NET")
            if "django" in content or "flask" in content or "fastapi" in content:
                frameworks.add("Python")

        return sorted(frameworks) if frameworks else ["Unknown"]
