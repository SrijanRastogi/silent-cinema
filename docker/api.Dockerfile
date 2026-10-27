# Local parity image for the API and the worker placeholder.
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ffmpeg \
        tesseract-ocr \
        tesseract-ocr-eng \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv==0.13.6"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY apps ./apps
COPY alembic.ini ./
COPY apps/api/migrations ./apps/api/migrations

RUN useradd --create-home --uid 10001 cinema \
    && mkdir -p /data \
    && chown -R cinema:cinema /app /data
USER cinema

EXPOSE 8000

CMD ["uvicorn", "silent_cinema.app:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "8000"]
