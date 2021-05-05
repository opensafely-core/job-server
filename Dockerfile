FROM python:3.9-buster

# Don't cache PyPI downloads or wheels.
# Don't use pyc files or __pycache__ folders.
# Don't buffer stdout/stderr output.
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Only requirements to cache them in docker layer so we can skip package
# installation if they haven't changed
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes --requirement requirements.txt

RUN apt-get update && \
    apt-get install --no-install-recommends -y sqlite3=3.27.2-3+deb10u1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

ENTRYPOINT ["/app/entrypoint.sh"]
