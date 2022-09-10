import datetime
import hashlib
import logging
import os
import pickle
from typing import cast, Tuple, Optional
import asyncio

import pytz
from astral import LocationInfo
from astral.location import Location
from surepy import Flap, Surepy
import surepy

# from google.cloud import firestore
#
# import sure_petcare

logger = logging.getLogger(__name__)
