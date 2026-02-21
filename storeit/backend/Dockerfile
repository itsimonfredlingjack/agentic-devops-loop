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
RUN useradd -r storeit && chown -R storeit:storeit /app
USER storeit
EXPOSE 8004
HEALTHCHECK --interval=10s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health')"
CMD ["uvicorn", "storeit.main:app", "--host", "0.0.0.0", "--port", "8004"]
