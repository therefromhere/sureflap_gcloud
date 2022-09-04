#!/usr/bin/env bash

./scripts/generate_requirements.sh
gcloud functions deploy update --runtime=python310 --trigger-http --env-vars-file=.env_vars.yaml
