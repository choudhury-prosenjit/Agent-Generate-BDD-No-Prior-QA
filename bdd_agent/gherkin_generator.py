import re
from pathlib import Path

from .deduplicator import DuplicateScenarioDetector


def _sanitize_feature_text(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"^```gherkin\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "module"


class GherkinFeatureWriter:
    def __init__(self) -> None:
        self.detector = DuplicateScenarioDetector()

    def write_feature(self, output_dir: Path, module_name: str, raw_text: str) -> Path:
        sanitized = _sanitize_feature_text(raw_text)
        deduplicated = self.detector.deduplicate(sanitized)
        filename = f"{_slugify(module_name)}.feature"
        output_path = output_dir / filename
        output_path.write_text(deduplicated, encoding="utf-8")
        return output_path

    def count_scenarios(self, feature_text: str) -> int:
        return len(re.findall(r"(?im)^\s*Scenario(?: Outline)?:", feature_text))
