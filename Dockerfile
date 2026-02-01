# Agentic Dev Loop - Secure Container Environment
#
# This container provides an isolated environment for the autonomous agent
# with restricted permissions and no access to production secrets.
#
# Build: docker build -t agentic-dev-loop .
# Run:   docker run -it --rm -v $(pwd):/workspace agentic-dev-loop

FROM python:3.12-slim AS base

# Security: Don't run as root
RUN useradd -m -s /bin/bash agent && \
    mkdir -p /workspace && \
    chown agent:agent /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (LTS) via NodeSource apt repo (avoids curl | bash)
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | \
    gpg --dearmor -o /usr/share/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | \
    tee /etc/apt/sources.list.d/nodesource.list > /dev/null && \
    apt-get update && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
    dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
    tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y gh && \
    rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    ruff \
    mypy \
    httpx

# Install Claude Code CLI
# Note: Replace with actual installation method when available
# RUN npm install -g @anthropic/claude-code

# Switch to non-root user
USER agent
WORKDIR /workspace

# Set up Python user packages
ENV PATH="/home/agent/.local/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Security: Disable telemetry
ENV DO_NOT_TRACK=1
ENV CHECKPOINT_DISABLE=1

# Git configuration (will be overridden by mounted config)
RUN git config --global init.defaultBranch main && \
    git config --global core.editor "cat" && \
    git config --global advice.detachedHead false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 --version && node --version && git --version

# Default command
CMD ["/bin/bash"]

# ============================================================================
# Multi-stage build for production
# ============================================================================

FROM base AS production

# Copy only necessary files (not secrets)
COPY --chown=agent:agent .claude/ /workspace/.claude/
COPY --chown=agent:agent docs/ /workspace/docs/
COPY --chown=agent:agent scripts/ /workspace/scripts/

# Make scripts executable
RUN chmod +x /workspace/scripts/*.sh 2>/dev/null || true
RUN chmod +x /workspace/.claude/hooks/*.py 2>/dev/null || true

# Verify setup
RUN python3 -c "import sys; print(f'Python {sys.version}')" && \
    node --version && \
    git --version

# ============================================================================
# Development stage with additional tools
# ============================================================================

FROM base AS development

# Install additional dev tools
RUN pip install --no-cache-dir \
    ipython \
    rich \
    watchdog

# Install npm dev tools globally
RUN npm install -g \
    typescript \
    ts-node \
    eslint \
    prettier

USER agent
WORKDIR /workspace
