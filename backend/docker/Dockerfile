# ---- BASE IMAGE -------------------------------------------------------------
FROM python:3.12-slim-trixie

# ---- ENVIRONMENT ------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    APP_PORT=8000

# The uv installer requires curl and certificates; entrypoint.sh uses bash.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin:/app/.venv/bin:${PATH}"

# ---- DEPENDENCIES -----------------------------------------------------------
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- APPLICATION ------------------------------------------------------------
COPY . .

# ---- ENTRYPOINT -------------------------------------------------------------
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ---- NETWORK ----------------------------------------------------------------
EXPOSE ${APP_PORT}

# ---- DEFAULT COMMAND --------------------------------------------------------
CMD ["/entrypoint.sh"]
