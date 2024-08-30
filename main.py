import logging

import flask
import sureflap_gcloud
import google.cloud.logging


def update2(request: flask.Request):
    """
    Google cloud function entrypoint
    """
    client = google.cloud.logging.Client()
    client.setup_logging()

    process()

    retval = {"status": "ok"}

    return flask.jsonify(retval)


def process():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    sureflap_gcloud.set_curfew()


if __name__ == "__main__":
    process()
