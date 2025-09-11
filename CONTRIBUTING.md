# Contributing to Gramps MCP

Thank you for your interest in contributing to Gramps MCP! This guide will help you get started with development and contributing to the project.

## Quick Start

1. **Fork and Clone**:
```bash
git clone https://github.com/yourusername/gramps-mcp.git
cd gramps-mcp
```

2. **Setup Development Environment**:
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies including dev tools
uv sync
```

3. **Setup Pre-commit Hooks** (recommended):
```bash
uv run pre-commit install
```

## Development Workflow

### Testing

This project follows **Test-Driven Development (TDD)** practices:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_search_basic.py

# Run with verbose output
uv run pytest -xvs

# Run specific test
uv run pytest tests/test_search_basic.py::TestFindPersonTool::test_find_person -xvs
```

**Important**: Tests use real Gramps Web API connections (no mocks). Ensure you have a test Gramps Web instance configured in your `.env` file.

### Code Quality

We maintain high code quality standards:

```bash
# Lint code
uv run ruff check src/

# Format code
uv run ruff format src/

# Type checking (if available)
uv run mypy src/
```

Pre-commit hooks will automatically run these checks on commit.

### Project Structure

Follow the established architecture:

```
src/gramps_mcp/
|-- server.py           # MCP server setup
|-- tools/              # Tool implementations by feature
|-- client.py           # Gramps Web API client
|-- auth.py             # Authentication handling
|-- models/             # Pydantic models
|-- handlers/           # Data formatting
`-- config.py          # Configuration
```

## Contributing Guidelines

### Code Style

- Follow **PEP 8** conventions
- Use **type hints** for all functions
- Write **Google-style docstrings**:
```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.

    Returns:
        Description of return value.
    """
```

### File Length Limit

- **Never create files longer than 500 lines**
- Refactor large files into smaller, focused modules
- Split by feature or responsibility

### Testing Requirements

- **Write tests first** (TDD approach)
- **No mocks** - use real API integration tests
- Test files mirror the `src/` structure in `tests/`
- All new features must include comprehensive tests

### Commit Messages

Follow the established pattern:
```
type: Brief description

Longer description if needed

Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

## Development Setup

### Environment Variables

Copy `.env.example` to `.env` and configure:
```bash
GRAMPS_API_URL=https://your-test-gramps-instance.com
GRAMPS_USERNAME=your-username
GRAMPS_PASSWORD=your-password
GRAMPS_TREE_ID=your-tree-id
```

### Running the Server

```bash
# HTTP transport (development)
uv run python -m src.gramps_mcp.server

# Stdio transport (testing)
uv run python -m src.gramps_mcp.server stdio
```

## Pull Request Process

1. **Create a feature branch**: `git checkout -b feature/your-feature-name`
2. **Write tests first** following TDD practices
3. **Implement the feature** ensuring tests pass
4. **Run quality checks**: `uv run ruff check src/ && uv run pytest`
5. **Update documentation** if needed
6. **Submit pull request** with clear description

### Pull Request Requirements

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated (if applicable)
- [ ] No files exceed 500 lines
- [ ] Features include comprehensive tests
- [ ] Commit messages follow convention

## Reporting Issues

Use GitHub Issues for:
- **Bug reports** with reproduction steps
- **Feature requests** with clear use cases
- **Documentation improvements**
- **Questions** about usage or development

## Getting Help

- **GitHub Discussions**: For questions and community discussion
- **GitHub Issues**: For bug reports and feature requests
- **Code Review**: Submit PRs for collaborative improvement

## License

By contributing, you agree that your contributions will be licensed under the GNU Affero General Public License v3.0.

## Recognition

All contributors are valued! Significant contributions will be recognized in the project acknowledgments.