#!/bin/bash

poetry export --without-hashes -o requirements.txt
gcloud functions deploy update --runtime=python310 --trigger-http --env-vars-file=.env_vars.yaml
