#!/usr/bin/bash

set -eu

ATTEMPTS=5
WAIT=10

ATTEMPT=0
SUCCESS=0

IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' job-server_prod_1)

# call curl with retry functionality, returning just the status code to check
# against below
CURL_ARGS=(
  -q
  # --silent
  # --output /dev/null
  # --write-out "%{http_code}"
  --compressed
  --fail
  --location
  --max-time 60
  --retry 5
  --retry-delay 5
)

echo "running curl with: " "${CURL_ARGS[@]}"

# recreated from the dokku check deploy code:
# https://github.com/dokku/dokku/blob/aa5a3953da039df345e7897fb7f437773826025a/plugins/scheduler-docker-local/check-deploy#L201-L222
until [[ $SUCCESS == 1 || $ATTEMPT -ge $ATTEMPTS ]]; do
  ATTEMPT=$((ATTEMPT + 1))

  echo "Attempt $ATTEMPT/$ATTEMPTS. Waiting for $WAIT seconds"
  sleep "$WAIT"

  # shellcheck disable=SC2086
  if OUTPUT=$(curl "${CURL_ARGS[@]}" "http://0.0.0.0:8000" 2>&1); then
    # OUTPUT contains the HTTP response
    # shellcheck disable=SC2076
    if [[ "$OUTPUT" =~ 200 ]]; then
      SUCCESS=1
      break
    fi
    echo "got output: $OUTPUT"
  else
    echo "Failed to connect/no response, output is: $OUTPUT"
  fi
done


if [[ $SUCCESS -ne 1 ]]; then
  echo "Failed to connect/no response, output is: $OUTPUT"
  docker-compose -f docker/docker-compose.yaml logs prod
  docker ps
  IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.Gateway}}{{end}}' job-server_prod_1)
  echo "gateway docker IP: $IP"
  ping -c 4 "$IP"
  # docker run --network container:job-server_prod_1 appropriate/curl -s --retry 10 --retry-connrefused http://localhost:8000/
  curl "${CURL_ARGS[@]}" "$IP:8000"
  exit 1
fi

echo "SUCCESS"
