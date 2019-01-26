#!/bin/bash

gcloud functions deploy update --runtime=python37 --trigger-http --env-vars-file=.env_vars.yaml
