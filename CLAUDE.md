### Project Awareness & Context
- **Always read `README.md`** at the start of a new conversation to understand the project's setup, features, and usage.
- **Use consistent naming conventions, file structure, and architecture patterns** following Python and MCP best practices.
- **Use uv** for all Python dependency management and command execution.
  - **Commands**: Use `uv run python` or `uv run <command>` for executing Python scripts and tests
  - **Dependencies**: Use `uv add <package>` to add dependencies, `uv sync` to install
  - **Git commits**: Use `uv run git commit` to ensure pre-commit hooks run correctly

### Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
  For this MCP server project:
    - `server.py` - Main MCP server setup and routing
    - `tools/` directory - MCP tool implementations organized by feature
    - `client.py` - Gramps Web API client
    - `auth.py` - JWT authentication handling
    - `models/` directory - Pydantic models for validation
    - `config.py` - Configuration management
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python_dotenv and load_dotenv()** for environment variables.

### Testing & Reliability (TDD Approach)
- **This project follows Test-Driven Development (TDD) practices**.
- **Write tests FIRST before implementing functionality** - red, green, refactor cycle.
- **Always create Pytest integration tests for new features** (functions, classes, routes, etc).
- **Use real APIs for testing - no mocks, fixtures, or test clients**.
- **After updating any logic**, check whether existing tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
- **Run tests frequently during development** using `uv run pytest` or `uv run pytest -xvs` for verbose output.


### Style & Conventions
- **Use Python** as the primary language.
- **Follow PEP8**, use type hints, format with `black`, and lint with `ruff`.
- **Use `pydantic` for data validation**.
- Use `httpx` for async HTTP client (no FastAPI needed for MCP servers).
- Use `MCP Python SDK` for MCP server implementation.
- Write **docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```

### Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to
- **Do not use emojis in the code** to maintain a clean and professional coding style.