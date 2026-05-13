from dataclasses import dataclass
from pathlib import Path

from .discovery import DiscoveryResult


@dataclass
class GenerationStats:
    total: int
    positive: int
    negative: int
    edge: int


class ReportGenerator:
    def generate(
        self,
        output_dir: Path,
        repository_url: str,
        branch: str,
        frameworks: list[str],
        discovery: DiscoveryResult,
        feature_files: list[Path],
        stats: GenerationStats,
        skipped_areas: list[str],
    ) -> Path:
        report_path = output_dir / "bdd_generation_report.md"
        lines = [
            "# BDD Generation Report",
            "",
            f"- **Repository URL:** {repository_url}",
            f"- **Branch analyzed:** {branch}",
            f"- **Technology/framework detected:** {', '.join(frameworks)}",
            f"- **Modules identified:** {', '.join(discovery.modules) or 'None'}",
            f"- **Pages/screens identified:** {', '.join(discovery.pages) or 'None'}",
            f"- **APIs identified:** {', '.join(discovery.apis) or 'None'}",
            f"- **Feature files generated:** {', '.join(path.name for path in feature_files) or 'None'}",
            f"- **Number of scenarios generated:** {stats.total}",
            f"- **Positive scenarios:** {stats.positive}",
            f"- **Negative scenarios:** {stats.negative}",
            f"- **Edge-case scenarios:** {stats.edge}",
            "",
            "## Assumptions or inferred behavior",
            *(f"- {item}" for item in discovery.assumptions),
            "",
            "## Code areas skipped due to missing information",
            *(f"- {item}" for item in skipped_areas),
            "",
            "## Recommendations for manual review",
            "- Validate inferred scenarios against product/business stakeholders.",
            "- Review security and authorization scenarios with the architecture team.",
            "- Confirm API error contracts for non-documented failure paths.",
        ]

        report_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        return report_path
