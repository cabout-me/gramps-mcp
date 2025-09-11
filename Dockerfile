FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including uv
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy the application code
COPY src/ src/

# Create a non-root user
RUN useradd -m -u 1000 gramps && chown -R gramps:gramps /app
USER gramps

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the MCP server
CMD ["uv", "run", "python", "-m", "src.gramps_mcp.server"]