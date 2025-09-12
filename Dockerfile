FROM python:3.11-slim

# Add OCI labels
LABEL org.opencontainers.image.title="Gramps MCP"
LABEL org.opencontainers.image.description="AI-Powered Genealogy Research & Management - MCP server for Gramps Web API"
LABEL org.opencontainers.image.url="https://github.com/cabout-me/gramps-mcp"
LABEL org.opencontainers.image.source="https://github.com/cabout-me/gramps-mcp"
LABEL org.opencontainers.image.documentation="https://github.com/cabout-me/gramps-mcp/blob/main/README.md"
LABEL org.opencontainers.image.licenses="AGPL-3.0"
LABEL org.opencontainers.image.vendor="cabout.me"

WORKDIR /app

# Install system dependencies including uv
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies in a single layer
RUN uv sync --frozen --no-dev

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