#!/usr/bin/env bash
# A script used for building tmpl with docker.

set -e

if [ ! -f Dockerfile ]; then
    echo 'Unable to locate the build "Dockerfile" - please run at the root of the repository.'
    exit 1
fi

docker build -t "tmpl:${1:-latest}" .
