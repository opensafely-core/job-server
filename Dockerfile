FROM node:16-buster AS nodeassets
WORKDIR /usr/src/app

COPY package*.json ./
RUN npm ci

COPY . ./
ARG VITE_SENTRY_DSN
RUN npm run build

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
COPY requirements.prod.txt .
RUN pip install --no-cache-dir --require-hashes --requirement requirements.prod.txt

COPY . /app

COPY --from=nodeassets /usr/src/app/assets/dist ./assets/dist

ENTRYPOINT ["/app/entrypoint.sh"]
