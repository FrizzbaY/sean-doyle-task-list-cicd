# Dockerfile

# Stage 1: install the Python packages into a virtual environment
FROM python:3.13-slim-trixie AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt


# Stage 2: the image that runs the app
FROM python:3.13-slim-trixie

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/tasks.db

# Install newer versions of the Debian packages already in the image
RUN apt-get update \
    && apt-get upgrade --yes \
    && rm --recursive --force /var/lib/apt/lists/*

# Unprivileged user, plus the two folders the app must be able to write to
RUN groupadd --system app \
    && useradd --system --gid app --no-create-home app \
    && mkdir /app /app/instance /data \
    && chown app:app /app/instance /data

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app.py .
COPY templates/ templates/

USER app
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--no-control-socket", "app:create_app()"]