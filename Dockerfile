FROM python:3.11-slim AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==2.4.1

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --only main

FROM python:3.11-slim AS runtime
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY . .
ENTRYPOINT ["python", "-m", "src.cli"]
# Call help by default
# Pass command upon container run to trigger the requested command
CMD [ "--help" ]
