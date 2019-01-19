import flask

import sureflap_gcloud


def update(request: flask.Request):
    """
    Google cloud function entrypoint

    :param request:
    :return:
    """
    retval = {"status": "ok"}

    sureflap_gcloud.update_firestore_cache()

    return flask.jsonify(retval)
