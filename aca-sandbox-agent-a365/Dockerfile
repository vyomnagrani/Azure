FROM python:3.12-slim AS runtime

ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODE=offline \
    PORT=8000

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY sample-data ./sample-data

RUN PIP_INDEX_URL=${PIP_INDEX_URL} pip install --no-cache-dir ".[live]"

USER 65532:65532

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
