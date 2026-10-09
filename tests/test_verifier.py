from pathlib import Path
from unittest.mock import MagicMock, patch

from timeless.agent.verifier import run_verification


@patch("subprocess.run")
def test_run_verification(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "1 passed"
    mock_proc.stderr = ""
    mock_run.return_value = mock_proc

    res = run_verification(tmp_path)
    assert res.success is True
    assert res.exit_code == 0
    assert "1 passed" in res.output
    mock_run.assert_called_once()
