# Timeless

A BYOK (Bring Your Own Key) terminal AI coding agent that keeps its attention focused on the specific coding problem that matters instead of trying to understand the entire codebase at once.

## Core Goal

`minimum relevant context` → `focused reasoning` → `targeted fix` → `verification`

## Installation

```bash
pip install timeless
```

### Quick Setup

Configure your preferred model provider and API key:

```bash
timeless setup
```

Run a task:

```bash
timeless "Fix failing unit tests in test_auth.py"
```

## Development Setup

### Prerequisites
- Python 3.13+

### Local Development Installation

1. Install in editable mode:
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
