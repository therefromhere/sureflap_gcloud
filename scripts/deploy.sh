#!/usr/bin/env bash

./scripts/generate_requirements.sh
gcloud functions deploy update --runtime=python311 \
  --trigger-http --env-vars-file=.env_vars.yaml \
  --set-secrets=projects/catflap/secrets/ASTRAL_LOCATION,SUREPY_AUTH_TOKEN=projects/catflap/secrets/SUREPY_AUTH_TOKEN:latest \
  --project=$GOOGLE_CLOUD_PROJECT
