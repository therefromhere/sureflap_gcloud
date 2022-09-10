import flask
import sureflap_gcloud


def update(request: flask.Request):
    """
    Google cloud function entrypoint
    """
    retval = {"status": "ok"}

    sureflap_gcloud.set_curfew()

    return flask.jsonify(retval)
