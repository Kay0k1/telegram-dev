FROM ghcr.io/astral-sh/uv:0.11.6 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY telegram_knowledge.py ./
RUN groupadd --gid 10001 telegram && useradd --uid 10001 --gid telegram --create-home telegram && mkdir /data && chown telegram:telegram /data
ENV TELEGRAM_KNOWLEDGE_DB=/data/corpus.sqlite3
USER telegram
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]
CMD ["/app/.venv/bin/python", "telegram_knowledge.py", "serve", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
