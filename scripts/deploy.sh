#!/usr/bin/env bash

./scripts/generate_requirements.sh
gcloud functions deploy update2 --gen2 --runtime=python312 --region=us-central1 \
  --trigger-http --env-vars-file=.env_vars.yaml \
  --allow-unauthenticated \
  --set-secrets=ASTRAL_LOCATION=ASTRAL_LOCATION:latest,SUREPY_AUTH_TOKEN=SUREPY_AUTH_TOKEN:latest \
  --project=$GOOGLE_CLOUD_PROJECT
