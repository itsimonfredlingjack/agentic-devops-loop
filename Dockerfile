FROM python:3.12-slim

LABEL maintainer="itsimonfredlingjack" \
      description="SEJFA (Secure Enterprise Jira Flask Agent) production container"

ARG GIT_SHA=unknown
ENV GIT_SHA=$GIT_SHA

RUN groupadd --system appuser \
    && useradd --system --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY requirements.txt /app/

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --no-compile -r requirements.txt

COPY . /app

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=30s --retries=3 CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "app:app"]
