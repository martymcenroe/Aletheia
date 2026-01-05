# Contributing to Aletheia

Thank you for your interest in contributing to Aletheia!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Install dependencies: `poetry install`
4. Create a feature branch: `git checkout -b feature/your-feature`

## Development Workflow

- **Documentation First:** Write or update the relevant LLD in `docs/` before writing code
- **Worktrees:** Use `git worktree add ../Aletheia-{IssueID} -b {IssueID}-short-desc` for feature work
- **Tests:** Run `poetry run pytest` before submitting
- **Linting:** Run `poetry run ruff check` and `npm run lint`

## Code Style

- Python: Follow PEP 8, enforced by ruff
- JavaScript: ESLint configuration in repository
- Commits: `type: description (ref #ID)` format

## Pull Requests

1. Ensure all tests pass
2. Update documentation if needed
3. Reference the issue number in PR description
4. Request review from maintainers

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps for bugs
- Check existing issues before creating new ones

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.
