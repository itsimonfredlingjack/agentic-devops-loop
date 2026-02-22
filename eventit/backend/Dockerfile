FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml requirements.txt* ./
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
RUN pip install --no-cache-dir .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=builder /usr/local/bin/alembic /usr/local/bin/alembic
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY entrypoint.sh .
RUN useradd -r eventit && chown -R eventit:eventit /app && chmod +x entrypoint.sh
USER eventit
EXPOSE 8005
HEALTHCHECK --interval=10s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')"
CMD ["./entrypoint.sh"]
