import logging

import flask
import sureflap_gcloud


def update(request: flask.Request):
    """
    Google cloud function entrypoint
    """
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    retval = {"status": "ok"}

    sureflap_gcloud.set_curfew()

    return flask.jsonify(retval)
