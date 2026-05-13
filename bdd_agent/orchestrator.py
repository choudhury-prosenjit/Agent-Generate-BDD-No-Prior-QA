import logging
import re
import tempfile
from pathlib import Path

from .code_scanner import CodeScanner
from .discovery import DiscoveryEngine
from .gherkin_generator import GherkinFeatureWriter
from .openai_client import OpenAIBDDClient
from .prompt_builder import PromptBuilder
from .repo_cloner import clone_repository
from .report_generator import GenerationStats, ReportGenerator

LOGGER = logging.getLogger(__name__)


class BDDAgentOrchestrator:
    def __init__(self, model: str) -> None:
        self.scanner = CodeScanner()
        self.discovery_engine = DiscoveryEngine()
        self.prompt_builder = PromptBuilder()
        self.writer = GherkinFeatureWriter()
        self.report_generator = ReportGenerator()
        self.openai_client = OpenAIBDDClient(model=model)

    def run(self, repository_url: str, branch: str, output_dir: Path) -> None:
        with tempfile.TemporaryDirectory(prefix="bdd_repo_") as temp_dir:
            cloned_repo = clone_repository(repository_url, branch, Path(temp_dir) / "repo")
            scanned_files = self.scanner.scan(cloned_repo)
            frameworks = self.scanner.detect_frameworks(scanned_files)
            discovery = self.discovery_engine.discover(scanned_files)

            module_targets = discovery.modules or ["application"]
            feature_files: list[Path] = []
            total = positive = negative = edge = 0

            for module in module_targets:
                prompt = self.prompt_builder.build_module_prompt(
                    repository_url=repository_url,
                    branch=branch,
                    frameworks=frameworks,
                    module_name=module,
                    discovery=discovery,
                )
                feature_raw = self.openai_client.generate_feature(module, prompt)
                feature_path = self.writer.write_feature(output_dir, module, feature_raw)
                feature_files.append(feature_path)

                feature_text = feature_path.read_text(encoding="utf-8")
                scenario_count = self.writer.count_scenarios(feature_text)
                total += scenario_count
                positive += len(re.findall(r"(?im)@positive", feature_text))
                negative += len(re.findall(r"(?im)@negative", feature_text))
                edge += len(re.findall(r"(?im)@edge", feature_text))

            skipped_areas = []
            if not discovery.pages:
                skipped_areas.append("Unable to confidently identify page/screen level artifacts.")
            if not discovery.apis:
                skipped_areas.append("Unable to confidently identify API contracts/endpoints.")

            stats = GenerationStats(total=total, positive=positive, negative=negative, edge=edge)
            report_path = self.report_generator.generate(
                output_dir=output_dir,
                repository_url=repository_url,
                branch=branch,
                frameworks=frameworks,
                discovery=discovery,
                feature_files=feature_files,
                stats=stats,
                skipped_areas=skipped_areas,
            )
            LOGGER.info("BDD generation completed. Report: %s", report_path)
