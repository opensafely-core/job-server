FROM ubuntu:bionic
ARG pythonversion

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true

RUN apt-get update
RUN apt-get -y upgrade
# Python dependencies
RUN apt-get install -y --no-install-recommends make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
# Pyenv dependencies
RUN apt-get install -y ca-certificates git
# Required by the runner
RUN apt-get install -y file
RUN apt-get install -y docker.io

# Install pyenv
RUN curl https://pyenv.run | bash
ENV PATH="/root/.pyenv/shims:/root/.pyenv/bin:${PATH}"
ENV PYENV_SHELL=bash

# Install python
RUN pyenv install $pythonversion
RUN pyenv global $pythonversion

# Install pip and requirements
RUN curl https://bootstrap.pypa.io/get-pip.py | python

# Copy happens twice to aid with image layers
COPY requirements.txt .
RUN pip install --requirement requirements.txt

RUN mkdir /app
COPY . /app
WORKDIR /app
RUN rm -rf .python-version
ENTRYPOINT ["/app/entrypoint.sh"]
