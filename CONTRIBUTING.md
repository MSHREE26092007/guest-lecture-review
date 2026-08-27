# Contributing to Guest Lecture Document Review Agent

Thank you for your interest in contributing! We welcome bug reports, feature suggestions, and pull requests.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MSHREE26092007/guest-lecture-review.git
   cd guest-lecture-review
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio anyio httpx
   ```

4. **Run the test suite**:
   ```bash
   pytest -v
   ```

## Workflow & Guidelines

- **Branches**: Create feature branches off `master` with descriptive names (e.g., `feat/add-docx-chart-checker`, `fix/table-parsing`).
- **Code Style**: Write clean, readable code following PEP 8 conventions.
- **Testing**: Ensure all new features or bug fixes have corresponding unit tests in the `tests/` directory.
- **Commit Messages**: Write concise, imperative commit messages (e.g., `Add unit tests for scoring rubric`).

## Submitting Pull Requests

1. Push your branch to your fork.
2. Open a Pull Request against `master`.
3. Ensure CI checks pass on all supported Python versions (3.10, 3.11, 3.12).
4. Provide a clear summary of changes and test results in the PR description.
