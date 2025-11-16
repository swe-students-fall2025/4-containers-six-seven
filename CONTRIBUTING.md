# Contribution Guidelines

This document outlines the Git workflow and code standards for the project.

## 4.3 Git Workflow

### Branch Naming Convention
- **Format**: `feature/<person-name>-<feature-description>`
- **Examples**:
  - `feature/alice-docker-setup`
  - `feature/bob-ocr-module`

### Pull Request Process
1.  Create feature branch from `main`.
2.  Implement task and commit regularly.
3.  Write/run tests (ensure 80%+ coverage).
4.  Format code with Black.
5.  Lint code with Pylint (score >= 8.0).
6.  Push feature branch to GitHub.
7.  Create pull request with a clear description.
8.  Request review from at least one teammate.
9.  Reviewer checks for CI/CD passes (green checks) and code quality.
10. Address review comments.
11. Merge PR.
12. Delete feature branch.

## 4.4 Code Standards

### Python Code Style
- **Formatter**: Black (default settings).
- **Linter**: Pylint (minimum score: 8.0/10).
- **Docstrings**: Google style.
- **Type Hints**: Use where possible.

### Testing Standards
- **Minimum 80% code coverage** (enforced by CI/CD).
- Unit tests for all functions.
- Mock external dependencies (camera, database, ML models).
- Use pytest fixtures for common setup.