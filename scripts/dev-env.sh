#!/bin/bash
set -euo pipefail
target="$1"

if ! command -v bw > /dev/null; then
    echo "You need the bitwarden cli tool installed:"
    echo 
    echo "    https://bitwarden.com/help/article/cli/#download-and-install"
    echo
    exit 1
fi

if test -z "$BW_SESSION"; then
    echo "Unlocking bitwarden..."
    BW_SESSION=$(bw unlock --raw)
    export BW_SESSION
fi

SOCIAL_AUTH_BW_ID=d48e3e3f-07ed-4865-b348-ace700ee004
GH_DEV_TOKEN_BW_ID=10242708-234a-4162-982f-ace700ee5c53

write() {
    local name="$1"
    local value="$2"
    sed -i "s/$name=.*/$name=$value/" "$target"
}

write GITHUB_TOKEN "$(bw get password $GH_DEV_TOKEN_ID)"
write SOCIAL_AUTH_GITHUB_KEY "$(bw get username $SOCIAL_AUTH_BW_ID)"
write SOCIAL_AUTH_GITHUB_SECRET "$(bw get password $SOCIAL_AUTH_BW_ID)"
