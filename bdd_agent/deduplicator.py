import re

_SCENARIO_BLOCK_PATTERN = re.compile(
    r"(?ms)(^\s*(?:@[\w@\- ]+\n)*)^\s*(Scenario(?: Outline)?:.*?)(?=^\s*(?:@[\w@\- ]+\n)*\s*Scenario(?: Outline)?:|\Z)"
)


class DuplicateScenarioDetector:
    def deduplicate(self, feature_text: str) -> str:
        matches = list(_SCENARIO_BLOCK_PATTERN.finditer(feature_text))
        if not matches:
            return feature_text.strip() + "\n"

        prefix = feature_text[: matches[0].start()].rstrip() + "\n\n"
        unique_blocks: list[str] = []
        seen: set[str] = set()

        for match in matches:
            block = f"{match.group(1)}{match.group(2)}".strip()
            normalized = re.sub(r"\s+", " ", block).strip().lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_blocks.append(block)

        return prefix + "\n\n".join(unique_blocks).strip() + "\n"
