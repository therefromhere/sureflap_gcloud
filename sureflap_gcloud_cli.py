#!/usr/bin/env python

import logging

import sureflap_gcloud


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    sureflap_gcloud.set_curfew()
