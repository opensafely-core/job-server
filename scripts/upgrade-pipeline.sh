#!/bin/bash
set -eu

file=$1
github_package_url="opensafely-pipeline@https://github.com/opensafely-core/pipeline/archive/refs/tags/"
latest=$(git ls-remote -h --refs --tags --heads https://github.com/opensafely-core/pipeline | grep -o "v20.*$" | sort | tail -1)
echo "Latest version of pipeline is $latest"

# exit early if we are at the latest version
if grep -q "$latest" "$file"; then
    echo "$file already contains latest version"
    exit
fi

sed -i "s#$github_package_url.*\.zip#$github_package_url$latest.zip#" "$file"
echo "Updated $file to pipline $latest"
