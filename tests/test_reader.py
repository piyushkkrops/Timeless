import os
from pathlib import Path

import pytest

from timeless.context.reader import FileReadError, read_file


def test_read_file_valid(tmp_path: Path) -> None:
    code_file = tmp_path / "hello.py"
    code_file.write_text("line 1\nline 2\nline 3\nline 4\nline 5\n", encoding="utf-8")

    res = read_file("hello.py", root_dir=tmp_path, start_line=2, max_lines=2)

    assert res.file_path == "hello.py"
    assert res.start_line == 2
    assert res.end_line == 3
    assert res.total_lines == 5
    assert "2: line 2" in res.content
    assert "3: line 3" in res.content
    assert "4: line 4" not in res.content


def test_read_file_path_traversal_rejected(tmp_path: Path) -> None:
    outside_dir = tmp_path.parent
    outside_file = outside_dir / "secret.txt"

    with pytest.raises(FileReadError) as exc_info:
        read_file(f"../{outside_file.name}", root_dir=tmp_path)
    assert "outside project root" in str(exc_info.value).lower()


def test_read_file_symlink_escape_rejected(tmp_path: Path) -> None:
    outside_file = tmp_path.parent / "outside_secret.txt"
    outside_file.write_text("secret_data", encoding="utf-8")

    symlink_path = tmp_path / "escaped_link.txt"
    try:
        os.symlink(outside_file, symlink_path)
    except OSError:
        pytest.skip("Symlinks not supported on platform")

    with pytest.raises(FileReadError) as exc_info:
        read_file("escaped_link.txt", root_dir=tmp_path)
    assert "outside project root" in str(exc_info.value).lower()


def test_read_file_excluded_file_rejected(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=123", encoding="utf-8")

    with pytest.raises(FileReadError) as exc_info:
        read_file(".env", root_dir=tmp_path)
    assert "restricted" in str(exc_info.value).lower()


def test_read_file_oversized_rejected(tmp_path: Path) -> None:
    large_file = tmp_path / "large.txt"
    large_file.write_bytes(b"A" * 600_000)

    with pytest.raises(FileReadError) as exc_info:
        read_file("large.txt", root_dir=tmp_path)
    assert "exceeds max allowed size" in str(exc_info.value).lower()


def test_read_file_binary_rejected(tmp_path: Path) -> None:
    bin_file = tmp_path / "binary.bin"
    bin_file.write_bytes(b"\x00\x01\x02\x03\x04")

    with pytest.raises(FileReadError) as exc_info:
        read_file("binary.bin", root_dir=tmp_path)
    assert "binary file" in str(exc_info.value).lower()


def test_read_file_invalid_line_range(tmp_path: Path) -> None:
    code_file = tmp_path / "test.py"
    code_file.write_text("print(1)\n", encoding="utf-8")

    with pytest.raises(FileReadError) as exc_info:
        read_file("test.py", root_dir=tmp_path, start_line=0)
    assert "start_line must be >= 1" in str(exc_info.value)

    with pytest.raises(FileReadError) as exc_info:
        read_file("test.py", root_dir=tmp_path, start_line=50)
    assert "Invalid start_line 50" in str(exc_info.value)
