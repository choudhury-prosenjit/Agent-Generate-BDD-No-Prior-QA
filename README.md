# Agent-Generate-BDD-No-Prior-QA

AI agent in Python that analyzes a GitHub repository and generates BDD test scenarios in Gherkin Given-When-Then format using the OpenAI API.

## Features

- Accepts input parameters:
  - GitHub repository URL
  - Branch name
  - Optional output directory
- Clones the target branch locally and analyzes source code in read-only mode.
- Filters irrelevant folders and binary files (`node_modules`, `target`, `build`, `dist`, `.git`, `logs`, `coverage`, `vendor`, etc.).
- Detects likely framework/technology (React, Angular, Spring Boot, Node.js, Python, .NET, etc.).
- Discovers modules, pages/screens, routes, APIs, forms, validations, user actions, workflows, and error-handling patterns.
- Generates module-level `.feature` files with rich BDD scenario coverage.
- Removes duplicate scenarios.
- Produces `bdd_generation_report.md` summarizing analysis and generation output.

## Project structure

- `generate_bdd_agent.py` - CLI entrypoint
- `bdd_agent/input_handler.py` - CLI argument parsing and validation
- `bdd_agent/repo_cloner.py` - branch clone handling
- `bdd_agent/file_filter.py` - folder/file filtering logic
- `bdd_agent/code_scanner.py` - code scanning and framework detection
- `bdd_agent/discovery.py` - module/page/API/workflow discovery
- `bdd_agent/prompt_builder.py` - OpenAI prompt construction
- `bdd_agent/openai_client.py` - OpenAI API integration
- `bdd_agent/gherkin_generator.py` - feature file writing
- `bdd_agent/deduplicator.py` - duplicate scenario detection
- `bdd_agent/report_generator.py` - summary report generation
- `bdd_agent/orchestrator.py` - end-to-end orchestration

## Setup

1. Use Python 3.10+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:

```bash
export OPENAI_API_KEY="<your_openai_api_key>"
```

## Run

```bash
python generate_bdd_agent.py --repo-url <github_repo_url> --branch <branch_name> --output ./generated-features
```

Example:

```bash
python generate_bdd_agent.py --repo-url https://github.com/example/app.git --branch main --output ./generated-features
```

## Notes

- If behavior is inferred from static code signals, generated scenarios are expected to mark this as `[INFERRED]`.
- Review generated scenarios with product and engineering teams before automation rollout.
