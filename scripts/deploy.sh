#!/usr/bin/env bash

./scripts/generate_requirements.sh
gcloud functions deploy update --runtime=python311 \
  --trigger-http --env-vars-file=.env_vars.yaml \
  --set-secrets=ASTRAL_LOCATION=projects/$GOOGLE_CLOUD_PROJECT/secrets/ASTRAL_LOCATION:latest,SUREPY_AUTH_TOKEN=projects/$GOOGLE_CLOUD_PROJECT/secrets/SUREPY_AUTH_TOKEN:latest \
  --project=$GOOGLE_CLOUD_PROJECT
