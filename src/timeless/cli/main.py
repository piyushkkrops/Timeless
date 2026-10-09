import argparse
import importlib.metadata
import sys

from timeless.agent import run_agent_task
from timeless.config import CONFIG_FILE, load_config, save_config
from timeless.models import MissingAPIKeyError, ModelProviderError, get_provider


def get_version() -> str:
    try:
        return importlib.metadata.version("timeless")
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0"


def handle_setup(args: argparse.Namespace) -> int:
    cfg = load_config()

    provider = (args.provider or cfg.default_provider or "openai").lower().strip()
    api_key = args.api_key

    if not api_key and sys.stdin.isatty():
        try:
            p_input = input(
                f"Select provider [openai/anthropic/gemini] (default: {provider}): "
            ).strip()
            if p_input:
                provider = p_input.lower()

            api_key = input(f"Enter API key for {provider}: ").strip()
        except EOFError:
            pass

    cfg.default_provider = provider
    if api_key:
        if provider == "openai":
            cfg.openai_api_key = api_key
        elif provider == "anthropic":
            cfg.anthropic_api_key = api_key
        elif provider == "gemini":
            cfg.gemini_api_key = api_key

    save_config(cfg)
    print(f"Configuration saved to '{CONFIG_FILE}'.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="timeless",
        description="Timeless: A BYOK terminal AI coding agent.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    parser.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic", "gemini"],
        help="LLM provider to use (openai, anthropic, gemini).",
    )
    parser.add_argument(
        "-s",
        "--search",
        help="Perform a focused search for terms/files in the repository.",
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Disable automatic project context gathering.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Auto-confirm proposed file edits without interactive prompt.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification test suite after executing task.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="The coding-task prompt to execute.",
    )
    return parser


def build_setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="timeless setup",
        description="Configure provider choices and API credentials.",
    )
    parser.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic", "gemini"],
        help="Target provider to set up.",
    )
    parser.add_argument(
        "--api-key",
        help="API key for the selected provider.",
    )
    return parser


def main(args: list[str] | None = None) -> int:
    argv = sys.argv[1:] if args is None else args
    if argv and argv[0] == "setup":
        setup_parser = build_setup_parser()
        parsed_setup = setup_parser.parse_args(argv[1:])
        return handle_setup(parsed_setup)

    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.prompt:
        parser.print_help()
        return 0

    cfg = load_config()
    target_provider = parsed_args.provider or cfg.default_provider or "openai"

    try:
        provider = get_provider(target_provider)
        run_res = run_agent_task(
            prompt=parsed_args.prompt,
            provider=provider,
            search_query=parsed_args.search,
            no_context=parsed_args.no_context,
            auto_confirm=parsed_args.yes,
            verify=parsed_args.verify,
        )

        print("\n" + run_res.response.text)

        if run_res.verification:
            v = run_res.verification
            status_str = "PASSED" if v.success else "FAILED"
            print(f"\n[VERIFICATION ({status_str})]")
            print(f"Command: {v.command}")
            if not v.success and v.output:
                print(f"Summary output:\n{v.output[:500]}")

        return 0

    except MissingAPIKeyError as e:
        print(
            f"Error: {e} Alternatively, run 'timeless setup' to configure.",
            file=sys.stderr,
        )
        return 1
    except ModelProviderError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception:
        print("Error: An unexpected error occurred.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
