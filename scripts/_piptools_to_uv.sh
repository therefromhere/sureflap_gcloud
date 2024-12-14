#!/usr/bin/env bash

# Sync requirements.txt to uv
# This is only intended to be run from within the uv-sync action, and note that the pyproject change
# it makes isn't intended to be checked in

# adapted from https://github.com/win845/uv-light/blob/b4fabd9fc4fca621dd91bfe0a90e6ce6f17dd5ce/bin/uv-sync.sh

source ./scripts/_common_init.sh

AUTHOR_NAME=$(git log -1 --pretty=format:"%an")

if [[ "$AUTHOR_NAME" == *dependabot* ]] ; then
    # Read requirements.txt, exclude comments, and format as TOML array
    constraints=$(grep -vE '^\s*#' requirements.txt | awk '{print "  \""$0"\","}')

    echo
    # Append constraint-dependencies to pyproject.toml
    cat <<EOF >> pyproject.toml

### generated scripts/uv-sync.sh , but not intended to be checked in! ###
constraint-dependencies = [
$constraints
]
EOF

    echo "Lock uv with a new requirements.txt as constraint"
    uv lock
fi

./scripts/_uv_to_piptools.sh
