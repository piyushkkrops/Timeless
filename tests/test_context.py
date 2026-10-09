from pathlib import Path

from timeless.context.gatherer import gather_project_context


def test_gather_context_basic(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Test Project", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"', encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')", encoding="utf-8")

    context = gather_project_context(tmp_path)

    assert "[PROJECT CONTEXT]" in context
    assert "[/PROJECT CONTEXT]" in context
    assert "README.md" in context
    assert "pyproject.toml" in context
    assert "src/main.py" in context
    assert "# Test Project" in context


def test_gather_context_excludes_secrets_and_git(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET_KEY=12345", encoding="utf-8")
    (tmp_path / ".env.local").write_text("SECRET_KEY=67890", encoding="utf-8")
    (tmp_path / "secret.key").write_text("PRIVATE_KEY_DATA", encoding="utf-8")
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib.py").write_text("dummy", encoding="utf-8")

    context = gather_project_context(tmp_path)

    assert ".env" not in context
    assert "SECRET_KEY=12345" not in context
    assert "SECRET_KEY=67890" not in context
    assert "secret.key" not in context
    assert "PRIVATE_KEY_DATA" not in context
    assert ".git/HEAD" not in context
    assert ".venv/lib.py" not in context


def test_gather_context_truncates_large_files(tmp_path: Path) -> None:
    large_readme = "A" * 3000
    (tmp_path / "README.md").write_text(large_readme, encoding="utf-8")

    context = gather_project_context(tmp_path)

    assert "[truncated]" in context
    assert len(context) < 3500
