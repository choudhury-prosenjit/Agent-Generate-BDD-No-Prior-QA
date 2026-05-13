import logging
import sys

from bdd_agent.input_handler import parse_args, resolve_output_path, validate_repo_url
from bdd_agent.openai_client import OpenAIError
from bdd_agent.orchestrator import BDDAgentOrchestrator
from bdd_agent.repo_cloner import CloneError


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> int:
    configure_logging()
    args = parse_args()

    try:
        validate_repo_url(args.repo_url)
        output_dir = resolve_output_path(args.output)
        orchestrator = BDDAgentOrchestrator(model=args.model)
        orchestrator.run(args.repo_url, args.branch, output_dir)
    except (ValueError, CloneError, OpenAIError, RuntimeError) as exc:
        logging.getLogger(__name__).error("Execution failed: %s", exc)
        return 1

    logging.getLogger(__name__).info("Feature generation finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
