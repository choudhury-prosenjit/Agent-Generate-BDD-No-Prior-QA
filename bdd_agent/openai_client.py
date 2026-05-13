import logging
import os

LOGGER = logging.getLogger(__name__)


class OpenAIError(RuntimeError):
    """Raised when OpenAI request fails."""


class OpenAIBDDClient:
    def __init__(self, model: str) -> None:
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - dependency import error
            raise OpenAIError(
                "Missing dependency 'openai'. Install requirements.txt before running the agent."
            ) from exc

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise OpenAIError("OPENAI_API_KEY environment variable is missing")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_feature(self, module_name: str, prompt: str) -> str:
        try:
            LOGGER.info("Requesting BDD generation for module: %s", module_name)
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior QA architect creating precise business-readable "
                            "Gherkin feature files for Cucumber automation."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:  # pragma: no cover - API error handling
            raise OpenAIError(f"OpenAI API request failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else ""
        if not content:
            raise OpenAIError("OpenAI returned an empty response")
        return content
