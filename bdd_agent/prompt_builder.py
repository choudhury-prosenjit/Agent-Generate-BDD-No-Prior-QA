from textwrap import dedent

from .discovery import DiscoveryResult


class PromptBuilder:
    def build_module_prompt(
        self,
        repository_url: str,
        branch: str,
        frameworks: list[str],
        module_name: str,
        discovery: DiscoveryResult,
    ) -> str:
        return dedent(
            f"""
            Repository URL: {repository_url}
            Branch: {branch}
            Detected technologies: {', '.join(frameworks)}
            Current functional module: {module_name}

            Generate enterprise-grade Gherkin BDD scenarios for this module only.

            Requirements:
            - Use Given-When-Then format.
            - Include positive, negative, validation, boundary, edge, error, authorization,
              data-driven, and alternate flow scenarios whenever supported by evidence.
            - Use Scenario Outline with Examples for multiple input combinations.
            - Add meaningful tags from: @module @page @api @positive @negative @edge @validation @security @regression
            - Do not duplicate scenarios.
            - Do not invent unsupported business rules.
            - If inferred, explicitly mark in the scenario title with [INFERRED].
            - Group related scenarios under one Feature.
            - Ensure each scenario is independently executable.

            Discovered modules: {discovery.modules}
            Discovered pages/screens/components: {discovery.pages}
            Discovered frontend/backend routes: {discovery.routes}
            Discovered APIs: {discovery.apis}
            Discovered forms: {discovery.forms}
            Discovered validations: {discovery.validations}
            Discovered user actions: {discovery.user_actions}
            Discovered workflows: {discovery.workflows}
            Discovered error handling logic: {discovery.error_handling}
            Assumptions/inferences so far: {discovery.assumptions}

            Return only valid Gherkin content for a single .feature file.
            """
        ).strip()
