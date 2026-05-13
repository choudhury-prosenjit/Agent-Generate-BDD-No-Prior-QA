import tempfile
import unittest
from pathlib import Path

from bdd_agent.code_scanner import CodeScanner, ScannedFile
from bdd_agent.deduplicator import DuplicateScenarioDetector
from bdd_agent.file_filter import FileFilter
from bdd_agent.report_generator import GenerationStats, ReportGenerator
from bdd_agent.discovery import DiscoveryResult


class FileFilterTests(unittest.TestCase):
    def test_should_exclude_ignored_and_binary_files(self) -> None:
        f = FileFilter()
        self.assertTrue(f.should_exclude_path(Path("node_modules/app/index.js")))
        self.assertTrue(f.should_exclude_path(Path("assets/logo.png")))
        self.assertFalse(f.should_exclude_path(Path("src/app.py")))


class DuplicateScenarioDetectorTests(unittest.TestCase):
    def test_deduplicate_duplicate_scenarios(self) -> None:
        source = """
Feature: Login

@positive
Scenario: successful login
  Given user enters valid credentials
  When user submits login form
  Then dashboard is shown

@positive
Scenario: successful login
  Given user enters valid credentials
  When user submits login form
  Then dashboard is shown
"""
        result = DuplicateScenarioDetector().deduplicate(source)
        self.assertEqual(result.lower().count("scenario:"), 1)


class ScannerFrameworkTests(unittest.TestCase):
    def test_detect_frameworks(self) -> None:
        files = [
            ScannedFile(path=Path("/tmp/package.json"), relative_path="package.json", content='{"dependencies":{"react":"18"}}'),
            ScannedFile(path=Path("/tmp/pom.xml"), relative_path="pom.xml", content="spring-boot"),
        ]
        frameworks = CodeScanner().detect_frameworks(files)
        self.assertIn("React", frameworks)
        self.assertIn("Java Spring Boot", frameworks)


class ReportGeneratorTests(unittest.TestCase):
    def test_generate_report_contains_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            report_path = ReportGenerator().generate(
                output_dir=output_dir,
                repository_url="https://github.com/org/repo",
                branch="main",
                frameworks=["React"],
                discovery=DiscoveryResult(modules=["src"], pages=["src/pages/Home.tsx"], apis=["/api/login"], assumptions=[]),
                feature_files=[output_dir / "src.feature"],
                stats=GenerationStats(total=3, positive=1, negative=1, edge=1),
                skipped_areas=["None"],
            )
            content = report_path.read_text(encoding="utf-8")
            self.assertIn("Repository URL", content)
            self.assertIn("Number of scenarios generated", content)


if __name__ == "__main__":
    unittest.main()
