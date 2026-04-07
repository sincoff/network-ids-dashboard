# Contributing to Network IDS Dashboard

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Coding Standards](#coding-standards)
- [Submitting a Pull Request](#submitting-a-pull-request)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/network-ids-dashboard.git
   cd network-ids-dashboard
   ```
3. **Add the upstream** remote:
   ```bash
   git remote add upstream https://github.com/<org>/network-ids-dashboard.git
   ```

## Development Setup

### Prerequisites

- Ubuntu 24.04 LTS (or compatible Linux distribution)
- Python 3.12+
- `libpcap-dev` (for packet capture)
- Node.js 18+ (optional, for frontend tooling)

### Backend

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv libpcap-dev

python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env to match your network interface (run `ip -br a` to find it)

# Start the development server (requires sudo for packet capture)
sudo -E .venv/bin/uvicorn backend.app.main:app --app-dir . --host 0.0.0.0 --port 8000 --reload
```

### Frontend

The frontend is served as static files by the backend. Open `http://localhost:8000` in your browser.

## Making Changes

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes in small, focused commits.
3. Write clear commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification:
   ```
   feat: add ICMP flood detection
   fix: resolve WebSocket reconnection loop
   docs: update deployment guide for Nginx
   ```

## Coding Standards

### Python (Backend)

- **Formatter**: `ruff format`
- **Linter**: `ruff check`
- **Type Checker**: `mypy --strict`
- **Style**: Follow PEP 8. Use type hints on all function signatures.
- **Imports**: Use absolute imports (`from app.config import settings`).

### JavaScript (Frontend)

- Use `const`/`let` — never `var`.
- Use strict equality (`===`).
- Use descriptive variable names.
- Keep functions small and focused.

### CSS

- Use CSS custom properties (variables) for all design tokens.
- Mobile-first responsive design.
- Use semantic class names.

## Submitting a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a Pull Request against the `main` branch.
3. Fill out the [Pull Request template](.github/PULL_REQUEST_TEMPLATE.md).
4. Ensure all CI checks pass.
5. Request review from a maintainer.

### PR Requirements

- [ ] Code follows the project's coding standards
- [ ] Changes are tested (where applicable)
- [ ] Documentation is updated (if needed)
- [ ] Commit messages follow Conventional Commits
- [ ] No sensitive data (API keys, passwords) is committed

## Questions?

Open a [Discussion](https://github.com/<org>/network-ids-dashboard/discussions) or reach out to the maintainers.
