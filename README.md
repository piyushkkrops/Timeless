# Timeless

A BYOK (Bring Your Own Key) terminal AI coding agent that keeps its attention focused on the specific coding problem that matters instead of trying to understand the entire codebase at once.

## Core Goal

`minimum relevant context` → `focused reasoning` → `targeted fix` → `verification`

## Development Setup

### Prerequisites
- Python 3.13+

### Installation & Verification

1. Install local editable package:
   ```bash
   pip install -e .
   ```

2. Run checks:
   ```bash
   # Linting
   ruff check .
   ruff format --check .

   # Type checking
   mypy

   # Tests
   pytest
   ```
