import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VerificationResult:
    success: bool
    command: str
    exit_code: int
    output: str


def run_verification(root_dir: Path | None = None) -> VerificationResult:
    """Run test-based verification suite in root_dir."""
    root = (root_dir or Path.cwd()).resolve()

    # Locate pytest runner
    pytest_bin = shutil.which("pytest")
    if not pytest_bin:
        # Fallback to python -m pytest
        cmd = [sys.executable, "-m", "pytest"]
        cmd_str = f"{sys.executable} -m pytest"
    else:
        cmd = [pytest_bin]
        cmd_str = pytest_bin

    try:
        proc = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        combined_output = (proc.stdout + "\n" + proc.stderr).strip()
        success = proc.returncode == 0
        return VerificationResult(
            success=success,
            command=cmd_str,
            exit_code=proc.returncode,
            output=combined_output,
        )
    except Exception as e:
        return VerificationResult(
            success=False,
            command=cmd_str,
            exit_code=-1,
            output=f"Failed to execute verification suite: {e}",
        )
