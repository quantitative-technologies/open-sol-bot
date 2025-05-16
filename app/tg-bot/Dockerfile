# Build base image first
FROM python:3.10-slim as builder
# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /bin/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PDM_USE_VENV=true \
    PDM_INSTALL_PATH=/app \
    PROJECT_ROOT=/app \
    DEBUG_PYDEVD_PATHS_TRANSLATION=True

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install PDM
# RUN curl -sSL https://pdm.fming.dev/install-pdm.py | python3 - && \
#     ln -s /root/.local/bin/pdm /usr/bin/pdm

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/libs /app/logs

# Build final image
FROM builder as final

# Install dependencies
COPY ./libs /app/libs
COPY ./app/tg-bot/pyproject.toml /app/

# To save time during development, we'll copy the pdm.lock file from the host
# and use it to install the dependencies.
#COPY ./app/tg-bot/pdm.lock /app/
#RUN pdm install --no-self --no-editable -G local -G dev
RUN uv sync 

#ENTRYPOINT [ "pdm", "run", "python", "-m" ]
