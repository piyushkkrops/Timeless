from pathlib import Path

import pytest

from timeless.agent.editor import FileEditError, apply_file_edit


def test_apply_file_edit_auto_confirm(tmp_path: Path) -> None:
    file_to_edit = tmp_path / "src" / "app.py"
    res = apply_file_edit(
        "src/app.py", "print('updated')", root_dir=tmp_path, auto_confirm=True
    )

    assert res is True
    assert file_to_edit.read_text(encoding="utf-8") == "print('updated')"


def test_apply_file_edit_outside_root_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileEditError) as exc_info:
        apply_file_edit("../outside.py", "data", root_dir=tmp_path, auto_confirm=True)
    assert "outside project root" in str(exc_info.value).lower()


def test_apply_file_edit_excluded_file_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileEditError) as exc_info:
        apply_file_edit(".env", "SECRET=123", root_dir=tmp_path, auto_confirm=True)
    assert "restricted" in str(exc_info.value).lower()
