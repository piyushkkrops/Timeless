from pathlib import Path

from timeless.context.gatherer import is_excluded_path


class FileEditError(Exception):
    """Raised when a file edit fails or is rejected for safety."""

    pass


def apply_file_edit(
    file_path: str | Path,
    new_content: str,
    root_dir: Path | None = None,
    auto_confirm: bool = False,
) -> bool:
    """Safely apply a file edit within the project root with permission checks."""
    root = (root_dir or Path.cwd()).resolve()
    target_path = Path(file_path)

    if not target_path.is_absolute():
        candidate = (root / target_path).resolve()
    else:
        candidate = target_path.resolve()

    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise FileEditError(
            f"Access denied: path '{file_path}' is outside project root."
        ) from e

    if candidate.exists():
        try:
            real_path = candidate.resolve(strict=True)
            real_path.relative_to(root)
        except ValueError as e:
            raise FileEditError(
                f"Access denied: path '{file_path}' escapes project root."
            ) from e
    else:
        real_path = candidate

    if is_excluded_path(real_path, root):
        raise FileEditError(
            f"Access restricted: cannot edit excluded file '{file_path}'."
        )

    rel_str = str(real_path.relative_to(root))

    if not auto_confirm:
        print(f"\nProposed file edit to: {rel_str}")
        try:
            ans = input(f"Apply changes to '{rel_str}'? [y/N]: ").strip().lower()
        except EOFError:
            ans = "n"

        if ans not in ("y", "yes"):
            print(f"Edit to '{rel_str}' cancelled by user.")
            return False

    real_path.parent.mkdir(parents=True, exist_ok=True)
    real_path.write_text(new_content, encoding="utf-8")
    print(f"Successfully updated '{rel_str}'.")
    return True
