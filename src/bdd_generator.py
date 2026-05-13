"""Generates BDD feature files from source code using OpenAI."""

import re
from openai import OpenAI


_SYSTEM_PROMPT = (
    "You are an expert QA engineer specialised in Behaviour-Driven Development (BDD). "
    "Your task is to read source code and produce comprehensive Gherkin feature files. "
    "Write clear Feature descriptions, multiple Scenarios (happy path and edge cases), "
    "and use Scenario Outline with Examples tables where repetition exists. "
    "Return ONLY valid Gherkin — no markdown fences, no prose, no extra explanations."
)

_USER_TEMPLATE = """\
Analyse the source code below and generate a complete Gherkin feature file for it.

Module / feature area: {module_name}

{code_context}

Requirements:
- Start the file with the `Feature:` keyword and a meaningful name.
- Include a one-to-three line description under the feature.
- Cover at least the main happy path and two or more edge-case Scenarios.
- Use `Scenario Outline` + `Examples:` wherever parameterised tests make sense.
- Steps must be in Given / When / Then format (And / But are allowed too).
- Do NOT wrap the output in markdown code blocks.
"""

MAX_CHARS_PER_MODULE = 40_000  # stay well within model context limits


def group_files_by_module(files: dict) -> dict:
    """Group file paths by their top-level directory (module).

    Files that live at the root level are grouped under 'root'.

    Parameters
    ----------
    files : dict
        Mapping of file path → content.

    Returns
    -------
    dict
        Mapping of module name → {path: content}.
    """
    modules: dict = {}
    for path, content in files.items():
        parts = path.split("/")
        module = parts[0] if len(parts) > 1 else "root"
        modules.setdefault(module, {})[path] = content
    return modules


def _build_code_context(files: dict) -> str:
    """Build a readable code context string from a {path: content} dict."""
    parts = []
    total = 0
    for path, content in files.items():
        snippet = content[:MAX_CHARS_PER_MODULE - total]
        parts.append(f"### File: {path}\n```\n{snippet}\n```")
        total += len(snippet)
        if total >= MAX_CHARS_PER_MODULE:
            break
    return "\n\n".join(parts)


def _clean_gherkin(raw: str) -> str:
    """Strip accidental markdown fences from the model response."""
    # Remove ```gherkin … ``` or ``` … ``` wrappers if present
    raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$", "", raw.strip())
    return raw.strip()


def generate_bdd_for_module(module_name: str, files: dict, client: OpenAI) -> str:
    """Call the OpenAI API and return a Gherkin feature file for one module.

    Parameters
    ----------
    module_name : str
        Name used in the prompt and feature description.
    files : dict
        Mapping of file path → content for this module.
    client : OpenAI
        Authenticated OpenAI client.

    Returns
    -------
    str
        Gherkin content of the generated feature file.
    """
    code_context = _build_code_context(files)
    user_message = _USER_TEMPLATE.format(
        module_name=module_name,
        code_context=code_context,
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=2048,
    )
    raw = response.choices[0].message.content or ""
    return _clean_gherkin(raw)


def generate_bdd_tests(files: dict, api_key: str) -> dict:
    """Generate BDD feature files for all modules in the given file set.

    Parameters
    ----------
    files : dict
        Mapping of file path → content (as returned by fetch_repository_code).
    api_key : str
        OpenAI API key.

    Returns
    -------
    dict
        Mapping of feature file name (e.g. ``auth.feature``) → Gherkin content.
    """
    if not files:
        return {}

    client = OpenAI(api_key=api_key)
    modules = group_files_by_module(files)
    feature_files = {}

    for module_name, module_files in modules.items():
        feature_name = f"{module_name}.feature"
        feature_files[feature_name] = generate_bdd_for_module(module_name, module_files, client)

    return feature_files
