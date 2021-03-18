#!/bin/bash

gcloud functions deploy update --runtime=python38 --trigger-http --env-vars-file=.env_vars.yaml
