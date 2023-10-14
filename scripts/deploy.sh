#!/usr/bin/env bash

./scripts/generate_requirements.sh
gcloud functions deploy update --runtime=python311 --trigger-http --env-vars-file=.env_vars.yaml --project=$GOOGLE_CLOUD_PROJECT
