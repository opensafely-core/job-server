# syntax=docker/dockerfile:1.2

## These build args are used in FROM lines, so need to be declared globally and have defaults set.
ARG NODE_VERSION
ARG UV_VERSION=0.9

#################################################
#
# Create base image with python installed.
#
# DL3007 ignored because base-docker we specifically always want to build on
# the latest base image, by design.
#
# hadolint ignore=DL3007
FROM ghcr.io/opensafely-core/base-docker:24.04 as base-python

# we are going to use an apt cache on the host, so disable the default debian
# docker clean up that deletes that cache on every apt install
RUN rm -f /etc/apt/apt.conf.d/docker-clean

# ensure fully working base python3.12 installation using deadsnakes ppa
# see: https://gist.github.com/tiran/2dec9e03c6f901814f6d1e8dad09528e
# use space efficient utility from base image
RUN --mount=type=cache,target=/var/cache/apt \
    echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu noble main" > /etc/apt/sources.list.d/deadsnakes-ppa.list &&\
    /usr/lib/apt/apt-helper download-file 'https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xf23c5a6cf475977595c89f51ba6932366a755776' /etc/apt/trusted.gpg.d/deadsnakes.asc

# configure PostgreSQL apt repository for appropriate client
RUN --mount=type=cache,target=/var/cache/apt \
    echo "deb https://apt.postgresql.org/pub/repos/apt noble-pgdg main" > /etc/apt/sources.list.d/postgresql-ppa.list &&\
    /usr/lib/apt/apt-helper download-file 'https://www.postgresql.org/media/keys/ACCC4CF8.asc' /etc/apt/trusted.gpg.d/postgresql.asc

# install any additional system dependencies
COPY docker/dependencies.txt /tmp/dependencies.txt
RUN --mount=type=cache,target=/var/cache/apt \
    /root/docker-apt-install.sh /tmp/dependencies.txt

# uv environment variable documentation:
# https://docs.astral.sh/uv/reference/environment/
# copy files rather than symlink since the cache and the target are on different filesystems
ENV UV_LINK_MODE=copy
# compile at installation time, not import time
ENV UV_COMPILE_BYTECODE=1
# we are providing python via deadsnakes ppa
# (as we require dynamic linking of openssl for security reasons)
ENV UV_PYTHON_DOWNLOADS=never
# set the directory for the venv
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"

##################################################
#
# Reusable uv CLI layer
#
# This allows us to specify the version in one place, and also works
# around a limitation that you cannot use build args directly in `COPY
# --from`.
#
# See: https://github.com/moby/buildkit/issues/2412 for more information
#
#
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-cli

#################################################
#
# Create node image.
#
FROM node:${NODE_VERSION} AS node-builder

WORKDIR /usr/src/app
RUN mkdir -p ./assets

# copy just what npm ci needs
COPY package-lock.json package.json ./
RUN --mount=type=cache,target=/usr/src/app/.npm \
    npm set cache /usr/src/app/.npm && \
    npm ci

# just copy in the files `npm run build` needs
COPY vite.config.mjs ./
COPY assets/src ./assets/src
COPY templates ./templates

RUN --mount=type=cache,target=./npm npm run build

##################################################
#
# Build image
#
# Ok, now we have local base image with python and our system dependencies on.
# We'll use this as the base for our builder image, where we'll build and
# install any python packages needed.
#
# We use a separate, disposable build image to avoid carrying the build
# dependencies into the production image.
FROM base-python as builder

# Install any system build dependencies
COPY docker/build-dependencies.txt /tmp/build-dependencies.txt
RUN --mount=type=cache,target=/var/cache/apt \
    /root/docker-apt-install.sh /tmp/build-dependencies.txt

# Pull in the binaries from the uv-cli stage
COPY --from=uv-cli /uv /uvx /usr/local/bin/

# Create a venv with uv
# (https://docs.astral.sh/uv/guides/integration/docker/#using-the-pip-interface)
RUN uv venv /opt/venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=/opt/venv
# Place entry points in the environment at the front of the path
ENV PATH="/opt/venv/bin:$PATH"

# The cache mount means a) /root/.cache is not in the image, and b) it's
# preserved between docker builds locally, for faster dev rebuild.
# install prod dependencies
# --frozen for deterministic installs
# (https://docs.astral.sh/uv/reference/cli/#uv-sync--frozen)
# --no-dev so we only install prod dependencies
#  (https://docs.astral.sh/uv/reference/cli/#uv-sync--no-dev)
# --no-install-project so we only install the dependencies, not the
# project (https://docs.astral.sh/uv/reference/cli/#uv-sync--no-install-project)
# --directory /root lets `uv` detect the pyproject.toml, uv.lock etc.
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=pyproject.toml,target=/root/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/root/uv.lock \
    uv sync --frozen --no-dev --no-install-project --directory /root


##################################################
#
# Base project image
#
# Ok, we've built everything we need, build an image with all dependencies but
# no code.
#
# Not including the code at this stage has two benefits:
#
# 1) this image only rebuilds when the handlful of files needed to build
#    job-server-base changes. If we do `COPY . /app` now, this will rebuild when
#    *any* file changes.
#
# 2) Ensures we *have* to mount the volume for dev image, as there's no embedded
#    version of the code. Otherwise, we could end up accidentally using the
#    version of the code included when the prod image was built.
FROM base-python as job-server-base

RUN mkdir -p /app
WORKDIR /app

# copy venv over from builder image. These will have root:root ownership, but
# are readable by all.
COPY --from=builder /opt/venv /opt/venv

# copy node assets over from node-builder image. These will have root:root ownership, but
# are readable by all.
COPY --from=node-builder /usr/src/app/assets/dist /opt/assets

# Asset and staticfile management
#
# We support two dev environment side-by-side. Docker-based, which is the same
# everywhere, and the same as production. And host-based, which can mean OSX
# or some version linux. Windows not supported, currently
#
# Both dev envs have tooling and config to generate js assets and to run
# django's collectstatic. In the host-based tooling, these are written to
# ./assets/dist and ./staticfiles respectively. When we run the dev image, we
# mount the host directory in, which means that by default, the tooling when
# run inside the dev container would write to those same directories, which
# would overwrite the host's files.
#
# This is problem because if the host is OSX, this will break some npm stuff,
# and the collectfiles will race between the host-based and docker-based to
# write those files. There can also be file permissions issues.
#
# To solve this we parameterize those locations via BUILT_ASSETS and
# STATIC_ROOT env vars, and within the docker image set them to paths outside
# of /app, so they do not clash in anyway with the host-based generated files.
#
# We do this in both dev and prod docker images. The ./staticfiles and
# ./assets/dist directories are excluded in .dockerignore, so the prod image
# only ever has the files it builds. As the app dir is mounted in the dev
# image, it can see them, but the use of these separate directories means it
# will never use them.
ENV VIRTUAL_ENV=/opt/venv/  \
    PATH="/opt/venv/bin:$PATH"  \
    PYTHONPATH=/app  \
    BUILT_ASSETS=/opt/assets  \
    STATIC_ROOT=/opt/staticfiles \
    DJANGO_SETTINGS_MODULE="jobserver.settings" \
    ASSETS_DEV_MODE=False \
    OTEL_SERVICE_NAME="job-server"

##################################################
#
# Production image
#
# Copy code in, add proper metadata
FROM job-server-base as job-server-prod

# Adjust this metadata to fit project. Note that the base-docker image does set
# some basic metadata.
LABEL org.opencontainers.image.title="job-server" \
    org.opencontainers.image.description="Job Server" \
    org.opencontainers.image.source="https://github.com/opensafely-core/job-server"

# Expose the port to Dokku
# https://dokku.com/docs/networking/port-management/#applications-using-expose
EXPOSE 8000

# copy application code
COPY . /app

# collect static files
RUN SECRET_KEY=dummy-key \
    SOCIAL_AUTH_GITHUB_KEY=dummy-key \
    SOCIAL_AUTH_GITHUB_SECRET=dummy-secret \
    RAP_API_BASE_URL=http://localhost:3000/ \
    RAP_API_TOKEN=dummy \
    python /app/manage.py collectstatic --no-input

ENTRYPOINT ["/app/docker/entrypoints/prod.sh"]

# We set command rather than entrypoint, to make it easier to run different
# things from the cli
CMD ["gunicorn", "--config", "gunicorn.conf.py", "jobserver.wsgi"]

# finally, tag with build information. These will change regularly, therefore
# we do them as the last action.
ARG BUILD_DATE=unknown
LABEL org.opencontainers.image.created=$BUILD_DATE
ARG GITREF=unknown
LABEL org.opencontainers.image.revision=$GITREF

ARG USERID=10001
ARG GROUPID=10001
USER ${USERID}:${GROUPID}

##################################################
#
# Dev image
#
# Now we build a dev image from our job-server-base image. This is basically
# installing dev dependencies and changing the entrypoint
FROM job-server-base as job-server-dev

# Pull in the binaries from the uv-cli stage to install dev requirements
COPY --from=uv-cli /uv /uvx /usr/local/bin/

# install dev dependencies
# --frozen for deterministic installs
# (https://docs.astral.sh/uv/reference/cli/#uv-sync--frozen)
# --no-install-project so we only install the dependencies, not the
# project (https://docs.astral.sh/uv/reference/cli/#uv-sync--no-install-project)
# --directory /root lets `uv` detect the pyproject.toml, uv.lock etc.
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=pyproject.toml,target=/root/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/root/uv.lock \
    uv sync --frozen --no-install-project --directory /root

# Install playwright chromium dependencies. This needs to be done AFTER
# playwright is pip-installed
RUN playwright install-deps chromium

# Override ENTRYPOINT rather than CMD so we can pass arbitrary commands to the entrypoint script
ENTRYPOINT ["/app/docker/entrypoints/dev.sh"]

# Run as non root user. Required when building image.
ARG USERID
ARG GROUPID
USER ${USERID}:${GROUPID}
