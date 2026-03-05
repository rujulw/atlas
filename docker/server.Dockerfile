FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY server/requirements.txt /tmp/requirements.txt
COPY server/requirements-dev.txt /tmp/requirements-dev.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install -r /tmp/requirements-dev.txt

COPY server /app

EXPOSE 8000
