import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

from .code_scanner import ScannedFile

_ROUTE_PATTERNS = [
    re.compile(r"path\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"router\.(?:get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
]

_API_PATTERNS = [
    re.compile(r"@(?:Get|Post|Put|Delete|Patch)Mapping\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"app\.(?:get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"fetch\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
]


@dataclass
class DiscoveryResult:
    modules: List[str] = field(default_factory=list)
    pages: List[str] = field(default_factory=list)
    routes: List[str] = field(default_factory=list)
    apis: List[str] = field(default_factory=list)
    forms: List[str] = field(default_factory=list)
    validations: List[str] = field(default_factory=list)
    user_actions: List[str] = field(default_factory=list)
    workflows: List[str] = field(default_factory=list)
    error_handling: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


class DiscoveryEngine:
    def discover(self, files: List[ScannedFile]) -> DiscoveryResult:
        modules: Set[str] = set()
        pages: Set[str] = set()
        routes: Set[str] = set()
        apis: Set[str] = set()
        forms: Set[str] = set()
        validations: Set[str] = set()
        user_actions: Set[str] = set()
        workflows: Set[str] = set()
        error_handling: Set[str] = set()

        for scanned_file in files:
            rel_path = scanned_file.relative_path
            path_parts = Path(rel_path).parts
            content = scanned_file.content
            lowered = content.lower()

            if path_parts:
                modules.add(path_parts[0])
            if any(token in rel_path.lower() for token in ("page", "screen", "view", "component")):
                pages.add(rel_path)

            for pattern in _ROUTE_PATTERNS:
                routes.update(match.strip() for match in pattern.findall(content) if match.strip())

            for pattern in _API_PATTERNS:
                apis.update(match.strip() for match in pattern.findall(content) if match.strip())

            if "<form" in lowered or "useform(" in lowered or "formgroup" in lowered:
                forms.add(rel_path)

            for marker in ("required", "minlength", "maxlength", "@notnull", "@size", "validator"):
                if marker in lowered:
                    validations.add(f"{rel_path}: {marker}")

            if "onclick" in lowered or "onsubmit" in lowered or "navigate(" in lowered:
                user_actions.add(rel_path)

            if "workflow" in lowered or "step" in lowered or "status" in lowered:
                workflows.add(rel_path)

            if "try" in lowered and ("catch" in lowered or "except" in lowered):
                error_handling.add(rel_path)
            if "error" in lowered and ("throw" in lowered or "raise" in lowered or "500" in lowered):
                error_handling.add(rel_path)

        assumptions: List[str] = []
        if not apis:
            assumptions.append("[INFERRED] No explicit API patterns were detected from static analysis.")
        if not routes:
            assumptions.append("[INFERRED] No explicit route declarations were detected from static analysis.")

        return DiscoveryResult(
            modules=sorted(modules),
            pages=sorted(pages),
            routes=sorted(routes),
            apis=sorted(apis),
            forms=sorted(forms),
            validations=sorted(validations),
            user_actions=sorted(user_actions),
            workflows=sorted(workflows),
            error_handling=sorted(error_handling),
            assumptions=assumptions,
        )
