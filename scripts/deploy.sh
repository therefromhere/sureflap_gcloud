#!/usr/bin/env bash

source ./scripts/_common_init.sh

./scripts/generate_requirements.sh
gcloud functions deploy update2 --gen2 --runtime=python312 --region=us-central1 \
  --trigger-http --env-vars-file=.env_vars.yaml \
  --allow-unauthenticated \
  --set-secrets=ASTRAL_LOCATION=projects/$GOOGLE_CLOUD_PROJECT/secrets/ASTRAL_LOCATION:latest,SUREPY_TOKEN=projects/$GOOGLE_CLOUD_PROJECT/secrets/SUREPY_AUTH_TOKEN:latest \
  --project=$GOOGLE_CLOUD_PROJECT \
  --serve-all-traffic-latest-revision
