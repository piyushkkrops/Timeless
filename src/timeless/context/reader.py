from dataclasses import dataclass
from pathlib import Path

from timeless.context.gatherer import is_excluded_path


class FileReadError(Exception):
    """Exception raised when reading a file fails or violates security bounds."""

    pass


@dataclass(frozen=True)
class FileReadResult:
    file_path: str
    start_line: int
    end_line: int
    total_lines: int
    content: str


HARD_MAX_LINES = 500
DEFAULT_MAX_LINES = 200
MAX_FILE_SIZE_BYTES = 500_000  # 500 KB limit


def is_binary_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except Exception:
        return True


def read_file(
    file_path: str | Path,
    root_dir: Path | None = None,
    start_line: int = 1,
    max_lines: int = DEFAULT_MAX_LINES,
) -> FileReadResult:
    """Read bounded contents of a file within the project root.

    Safely checks path traversal, symlink escapes, excluded paths, binary status,
    file size, and line ranges.
    """
    root = (root_dir or Path.cwd()).resolve()
    target_path = Path(file_path)

    if not target_path.is_absolute():
        candidate = (root / target_path).resolve()
    else:
        candidate = target_path.resolve()

    # Path traversal & symlink escape verification
    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise FileReadError(
            f"Access denied: path '{file_path}' is outside project root."
        ) from e

    # Verify real path does not escape root (symlinks)
    try:
        real_path = candidate.resolve(strict=True)
        real_path.relative_to(root)
    except (ValueError, FileNotFoundError) as e:
        raise FileReadError(
            f"Access denied: file '{file_path}' does not exist or escapes project root."
        ) from e

    if not real_path.is_file():
        raise FileReadError(f"File not found: '{file_path}'.")

    if is_excluded_path(real_path, root):
        raise FileReadError(f"Access restricted: file '{file_path}' is excluded.")

    if real_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise FileReadError(
            f"File '{file_path}' exceeds max allowed size ({MAX_FILE_SIZE_BYTES} B)."
        )

    if is_binary_file(real_path):
        raise FileReadError(f"Cannot read binary file '{file_path}'.")

    if start_line < 1:
        raise FileReadError("start_line must be >= 1.")

    if max_lines < 1:
        raise FileReadError("max_lines must be >= 1.")

    effective_max_lines = min(max_lines, HARD_MAX_LINES)

    try:
        lines = real_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception as e:
        raise FileReadError(f"Failed to read file '{file_path}': {e}") from e

    total_lines = len(lines)
    if start_line > total_lines and total_lines > 0:
        raise FileReadError(
            f"Invalid start_line {start_line}: file only has {total_lines} lines."
        )

    start_idx = start_line - 1
    end_idx = min(start_idx + effective_max_lines, total_lines)
    selected_lines = lines[start_idx:end_idx]

    formatted_lines = [
        f"{idx}: {line}"
        for idx, line in zip(
            range(start_line, end_idx + 1), selected_lines, strict=False
        )
    ]
    content_str = "\n".join(formatted_lines)

    rel_file_path = str(real_path.relative_to(root))
    return FileReadResult(
        file_path=rel_file_path,
        start_line=start_line if total_lines > 0 else 0,
        end_line=end_idx if total_lines > 0 else 0,
        total_lines=total_lines,
        content=content_str,
    )
