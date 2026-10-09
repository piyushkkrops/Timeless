from pathlib import Path

from timeless.context.search import format_search_results, search_repository


def test_search_content_and_filename(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "def main():\n    print('hello world')\n", encoding="utf-8"
    )
    (tmp_path / "utils.py").write_text(
        "def helper():\n    return 'hello'\n", encoding="utf-8"
    )

    matches = search_repository("hello", root_dir=tmp_path)
    assert len(matches) == 2

    snippets = [m.line_snippet for m in matches]
    assert any("print('hello world')" in s for s in snippets)
    assert any("return 'hello'" in s for s in snippets)


def test_search_filename_matching(tmp_path: Path) -> None:
    (tmp_path / "special_config.json").write_text("{}", encoding="utf-8")

    matches = search_repository("special_config", root_dir=tmp_path)
    assert len(matches) >= 1
    assert matches[0].file_path == "special_config.json"
    assert matches[0].line_number is None
    assert "Filename matches" in matches[0].line_snippet


def test_search_excludes_ignored_dirs_and_secrets(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=12345", encoding="utf-8")
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("SECRET=gitconfig", encoding="utf-8")
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib.py").write_text("SECRET=venvlib", encoding="utf-8")

    matches = search_repository("SECRET", root_dir=tmp_path)
    assert len(matches) == 0


def test_search_max_results_limit(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        (src / f"file_{i}.py").write_text("target_token = True\n", encoding="utf-8")

    matches = search_repository("target_token", root_dir=tmp_path, max_results=3)
    assert len(matches) == 3


def test_search_empty_or_no_match(tmp_path: Path) -> None:
    (tmp_path / "code.py").write_text("x = 1\n", encoding="utf-8")

    matches = search_repository("nonexistent_term", root_dir=tmp_path)
    assert len(matches) == 0

    fmt = format_search_results("nonexistent_term", matches)
    assert "No matches found." in fmt
