#!/usr/bin/env bash

# generate requirements with hashes, for use by cloud function deploy

uv export --output-file=requirements.txt --quiet
