FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml requirements.txt* ./
COPY src/ src/
RUN pip install --no-cache-dir .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY src/ src/
RUN useradd -r trackit && chown -R trackit:trackit /app
USER trackit
EXPOSE 8002
HEALTHCHECK --interval=10s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"
CMD ["uvicorn", "trackit.main:app", "--host", "0.0.0.0", "--port", "8002"]
