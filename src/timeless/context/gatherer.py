from pathlib import Path

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    ".vscode",
    ".idea",
    "node_modules",
}

IGNORED_FILE_PREFIXES = (".env", "id_rsa")
IGNORED_FILE_EXTENSIONS = (
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dylib",
    ".dll",
    ".key",
    ".pem",
    ".crt",
    ".pfx",
)

MAX_FILE_LISTING = 50
MAX_CONTENT_BYTES = 2000


def is_excluded_path(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    if any(part in IGNORED_DIRS for part in rel_parts):
        return True
    name = path.name
    if any(name.startswith(prefix) for prefix in IGNORED_FILE_PREFIXES):
        return True
    if any(name.endswith(ext) for ext in IGNORED_FILE_EXTENSIONS):
        return True
    return False


def get_source_files(root: Path) -> list[str]:
    files: list[str] = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and not is_excluded_path(p, root):
            rel_str = str(p.relative_to(root))
            files.append(rel_str)
            if len(files) >= MAX_FILE_LISTING:
                break
    return files


def read_bounded_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        if len(content) > MAX_CONTENT_BYTES:
            return content[:MAX_CONTENT_BYTES] + "\n... [truncated]"
        return content
    except Exception:
        return None


def gather_project_context(root_dir: Path | None = None) -> str:
    root = (root_dir or Path.cwd()).resolve()
    sections: list[str] = [f"Working Directory: {root.name}"]

    source_files = get_source_files(root)
    if source_files:
        file_list_str = "\n".join(f"- {f}" for f in source_files)
        sections.append(f"Source Files:\n{file_list_str}")

    for target_name in ["pyproject.toml", "README.md"]:
        target_path = root / target_name
        if target_path.is_file() and not is_excluded_path(target_path, root):
            content = read_bounded_file(target_path)
            if content is not None:
                sections.append(f"File Content ({target_name}):\n{content}")

    return "[PROJECT CONTEXT]\n" + "\n\n".join(sections) + "\n[/PROJECT CONTEXT]"
