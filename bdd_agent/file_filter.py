from pathlib import Path

EXCLUDED_DIRS = {
    "node_modules",
    "target",
    "build",
    "dist",
    ".git",
    "logs",
    "coverage",
    "vendor",
    "__pycache__",
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".jar",
    ".war",
    ".class",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
}


class FileFilter:
    def should_exclude_path(self, path: Path) -> bool:
        if any(part in EXCLUDED_DIRS for part in path.parts):
            return True
        return path.suffix.lower() in BINARY_EXTENSIONS

    def is_text_file(self, path: Path) -> bool:
        return not self.should_exclude_path(path)
