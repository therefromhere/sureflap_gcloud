import logging

import flask
import sureflap_gcloud
import google.cloud.logging


def update(request: flask.Request):
    """
    Google cloud function entrypoint
    """
    client = google.cloud.logging.Client()
    client.setup_logging()

    retval = {"status": "ok"}

    sureflap_gcloud.set_curfew()

    return flask.jsonify(retval)
