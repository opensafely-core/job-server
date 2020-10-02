FROM python:3.8.6-slim-buster

# Don't cache PyPI downloads or wheels.
# Don't use pyc files or __pycache__ folders.
# Don't buffer stdout/stderr output.
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Only requirements to cache them in docker layer so we can skip package
# installation if they haven't changed
COPY requirements.txt .
RUN pip install --requirement requirements.txt

RUN apt-get update && \
    apt-get install --no-install-recommends -y sqlite3=3.27.2-3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

ENTRYPOINT ["/app/entrypoint.sh"]
