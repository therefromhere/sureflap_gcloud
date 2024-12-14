#!/usr/bin/env bash

# Update python package versions

# adapted from https://github.com/win845/uv-light/blob/b4fabd9fc4fca621dd91bfe0a90e6ce6f17dd5ce/bin/uv-sync.sh

source ./scripts/_common_init.sh

uv lock --upgrade

./scripts/_uv_to_piptools.sh
