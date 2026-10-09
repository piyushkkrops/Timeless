import re
from dataclasses import dataclass
from pathlib import Path

from timeless.context.gatherer import is_excluded_path


@dataclass(frozen=True)
class SearchMatch:
    file_path: str
    line_number: int | None
    line_snippet: str


def search_repository(
    query: str,
    root_dir: Path | None = None,
    max_results: int = 20,
    case_sensitive: bool = False,
) -> list[SearchMatch]:
    """Search filenames and file contents within the project root.

    Returns matching file paths, line numbers, and snippets bounded by max_results.
    """
    root = (root_dir or Path.cwd()).resolve()
    query_clean = query.strip()
    if not query_clean:
        return []

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(re.escape(query_clean), flags)
    except re.error:
        return []

    matches: list[SearchMatch] = []

    for p in sorted(root.rglob("*")):
        if len(matches) >= max_results:
            break

        if not p.is_file() or is_excluded_path(p, root):
            continue

        rel_path = str(p.relative_to(root))

        # Check filename match
        if pattern.search(rel_path):
            matches.append(
                SearchMatch(
                    file_path=rel_path,
                    line_number=None,
                    line_snippet=f"Filename matches '{query_clean}'",
                )
            )
            if len(matches) >= max_results:
                break

        # Search content line by line
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if pattern.search(line):
                        snippet = line.strip()
                        if len(snippet) > 120:
                            snippet = snippet[:117] + "..."
                        matches.append(
                            SearchMatch(
                                file_path=rel_path,
                                line_number=line_num,
                                line_snippet=snippet,
                            )
                        )
                        if len(matches) >= max_results:
                            break
        except Exception:
            continue

    return matches


def format_search_results(query: str, matches: list[SearchMatch]) -> str:
    if not matches:
        return f"[SEARCH RESULTS for '{query}']\nNo matches found.\n[/SEARCH RESULTS]"

    lines = [f"[SEARCH RESULTS for '{query}']"]
    for m in matches:
        if m.line_number is not None:
            lines.append(f"- {m.file_path}:{m.line_number}: {m.line_snippet}")
        else:
            lines.append(f"- {m.file_path}: {m.line_snippet}")
    lines.append("[/SEARCH RESULTS]")
    return "\n".join(lines)
