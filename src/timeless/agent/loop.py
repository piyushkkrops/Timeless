from dataclasses import dataclass, field
from pathlib import Path

from timeless.agent.verifier import VerificationResult, run_verification
from timeless.context import (
    format_search_results,
    gather_project_context,
    search_repository,
)
from timeless.models import ModelProvider, ModelResponse


@dataclass
class AgentRunResult:
    response: ModelResponse
    files_changed: list[str] = field(default_factory=list)
    verification: VerificationResult | None = None


def run_agent_task(
    prompt: str,
    provider: ModelProvider,
    root_dir: Path | None = None,
    search_query: str | None = None,
    no_context: bool = False,
    auto_confirm: bool = False,
    verify: bool = False,
) -> AgentRunResult:
    """Execute coding task: context -> model generation -> verification."""
    root = (root_dir or Path.cwd()).resolve()

    if no_context:
        final_prompt = prompt
    else:
        context = gather_project_context(root)
        if search_query:
            matches = search_repository(search_query, root_dir=root)
            search_fmt = format_search_results(search_query, matches)
            context = f"{context}\n\n{search_fmt}"
        final_prompt = f"{context}\n\n[USER PROMPT]\n{prompt}\n[/USER_PROMPT]"

    response = provider.generate(final_prompt)

    verification_res = None
    if verify:
        verification_res = run_verification(root)

    return AgentRunResult(
        response=response,
        files_changed=[],
        verification=verification_res,
    )
