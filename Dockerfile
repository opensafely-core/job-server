FROM python:3.8.6-slim-buster

# Don't cache PyPI downloads or wheels.
# Don't use pyc files or __pycache__ folders.
# Don't buffer stdout/stderr output.
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true

RUN apt-get update
# Required by the runner
RUN apt-get install -y file
RUN apt-get install -y docker.io

# Copy happens twice to aid with image layers
COPY requirements.txt .
RUN pip install --requirement requirements.txt

RUN mkdir /app
COPY . /app
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
