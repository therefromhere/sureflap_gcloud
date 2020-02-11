import datetime
import hashlib
import logging
import os
import pickle
from typing import Tuple, Optional

import pytz
from astral import LocationInfo
from astral.location import Location
from google.cloud import firestore

import sure_petcare

logger = logging.getLogger(__name__)


class SurePetFlapFireBaseCache(sure_petcare.SurePetFlap):
    """
    Override SurePetFlapAPI's cache load/save,
    to store in Google Firestore instead of on disk
    """

    # TODO
    DOC_ID = "1"

    def __init__(self, *args, **kwargs):
        self.db = firestore.Client()
        self.curfew_start = None
        self.curfew_end = None

        super().__init__(*args, **kwargs)

    def get_tz(self, household_id=None) -> datetime.tzinfo:
        household_id = household_id or self.default_household

        return pytz.timezone(self.households[household_id]["olson_tz"])

    def get_local_date(self, household_id=None) -> datetime.date:
        household_id = household_id or self.default_household

        tz = self.get_tz(household_id=household_id)
        utc_now = pytz.utc.localize(datetime.datetime.utcnow())
        local_now = utc_now.astimezone(tz)

        return local_now.date()

    def get_astral_location(self) -> Location:
        """
        ASTRAL_LOCATION is a comma separated string in the format of Astral's LocationInfo
        name,region,timezone,latitude,longitude
        eg: 'London,England,Europe/London,51°30'N,00°07'W'

        name and country are purely for labelling, can anything
        lat/long can be either in degrees and minutes or as a float (positive = North/East)
        elevation is in metres
        :return:
        """
        location_tuple = os.environ["ASTRAL_LOCATION"].split(",")
        location_info = LocationInfo(*location_tuple)
        location = Location(location_info)

        return location

    def set_curfew(self, household_id=None):
        household_id = household_id or self.default_household

        astral_location = self.get_astral_location()

        # pass in local date otherwise system date is used,
        # which causes a problem in NZ on the day the clocks change! (yesterday wasn't in DST)
        sun_times = astral_location.sun(local=True, date=self.get_local_date())
        self.curfew_start = sun_times["sunset"]
        self.curfew_end = sun_times["sunrise"]

        # TODO support multiple flaps
        flap_id = self.get_default_flap(household_id=household_id)

        url = f"{sure_petcare._URL_DEV}/{flap_id}/control"

        curfew_data = {
            "curfew": [
                {
                    "lock_time": self.curfew_start.time().strftime("%H:%M"),
                    "unlock_time": self.curfew_end.time().strftime("%H:%M"),
                    "enabled": True,
                }
            ]
        }

        logger.info(
            f"curfew: {self.curfew_start} .. {self.curfew_end} - put data: {curfew_data}"
        )
        print(
            f"curfew: {self.curfew_start} .. {self.curfew_end} - put data: {curfew_data}"
        )

        self._put_data(url=url, json=curfew_data)

    def _put_data(self, url, params=None, json=None):
        headers = self._create_header()
        self._api_put(url, headers=headers, params=params, json=json)

    def _api_put(self, url, *args, **kwargs):
        r = self.s.put(url, *args, **kwargs)
        if r.status_code == 401:
            # Retry once
            self.update_authtoken(force=True)
            if "headers" in kwargs and "Authorization" in kwargs["headers"]:
                kwargs["headers"]["Authorization"] = "Bearer " + self.cache["AuthToken"]
                r = self.s.get(url, *args, **kwargs)
            else:
                raise sure_petcare.SPAPIException(
                    "Auth required but not present in header"
                )
        return r

    def get_current_status_dict(self, pet_id, household_id=None) -> dict:
        household_id = household_id or self.default_household

        if pet_id not in self.all_pet_status[household_id]:
            raise sure_petcare.SPAPIUnknownPet()

        pet_data = self.all_pet_status[household_id][pet_id]
        since_utc = datetime.datetime.fromisoformat(pet_data["since"])

        return {
            "location": self.get_current_status(
                pet_id=pet_id, household_id=household_id
            ),
            "since": since_utc,
        }

    def get_firebase_doc_ref(self) -> firestore.DocumentReference:
        return self.db.collection("account_cache").document(self.DOC_ID)

    def _load_cache(self):
        """
        Read cache data from Google Firestore
        :return:
        """

        doc = self.get_firebase_doc_ref().get()

        # copied from parent
        self.cache = {
            "AuthToken": None,
            "households": None,
            "default_household": self._init_default_household,
            "router_status": {},  # indexed by household
            "flap_status": {},  # indexed by household
            "pet_status": {},  # indexed by household
            "pet_timeline": {},  # indexed by household
            "house_timeline": {},  # indexed by household
            "version": 1,  # of cache structure.
        }

        if doc.exists:
            doc_dict = doc.to_dict()

            try:
                self.cache = pickle.loads(doc_dict["pickled_cache"])
            except pickle.PickleError:
                pass

    def get_api_update_datetime_range(
        self
    ) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
        endpoint_times = set()

        for k, v in self.cache.items():
            if k.startswith("https://"):
                # assume it's an endpoint cache

                if v.get("ts"):
                    ts = v["ts"]
                    # force timezone
                    ts = ts.replace(tzinfo=pytz.utc)
                    endpoint_times.add(ts)

        if endpoint_times:
            endpoint_time_range = min(endpoint_times), max(endpoint_times)
        else:
            endpoint_time_range = None, None

        return endpoint_time_range

    def get_dict_for_firebase(self) -> dict:
        # TODO tidy this up
        household_id = self.default_household
        pets = self.get_pets(household_id=household_id)

        pet_statuses = []

        for pet_id, pet in pets.items():
            pet_status = self.get_current_status_dict(
                pet_id=pet_id, household_id=household_id
            )
            pet_status["name"] = pet["name"]
            pet_statuses.append(pet_status)

        endpoint_time_range = self.get_api_update_datetime_range()

        return {
            "AuthToken": self.cache["AuthToken"],
            "version": self.cache["version"],
            # dump the whole cache as a pickled string
            # since FireStore doesn't support int keys etc
            "pickled_cache": pickle.dumps(self.cache),
            # TODO - restructure this to support multiple households, flaps
            "default_flap_locked": self.locked(),
            "default_flap_lock_mode": self.lock_mode(),
            "device_id": self.device_id,
            "gcloud_function_version": os.environ.get("X_GOOGLE_FUNCTION_VERSION"),
            "oldest_cached_api_data": endpoint_time_range[0],
            "newest_cached_api_data": endpoint_time_range[1],
            "pet_statuses": pet_statuses,
            "curfew_start": self.curfew_start,
            "curfew_end": self.curfew_end,
        }

    def __exit__(self, *args, **kwargs):
        # TODO - copy cache locking behaviour?
        super().__exit__(*args, **kwargs)

        self.__read_only = True

        doc_ref = self.get_firebase_doc_ref()
        doc_ref.set(self.get_dict_for_firebase())


def gen_device_id_from_bytes(b: bytes) -> str:
    return str(int(hashlib.sha1(b).hexdigest(), 16))[:10]


def update_firestore_cache():
    email_address = os.environ.get("SUREFLAP_EMAIL")
    password = os.environ.get("SUREFLAP_PASSWORD")
    device_id = None

    if os.environ.get("FUNCTION_IDENTITY"):
        # google cloud function - set a deviceid since the sureflap api's way won't work
        device_id = gen_device_id_from_bytes(
            os.environ.get("FUNCTION_IDENTITY").encode()
        )

    with SurePetFlapFireBaseCache(
        email_address=email_address, password=password, device_id=device_id
    ) as api:
        # api.update()
        api.update_authtoken()
        api.update_households()
        api.update_device_ids()
        api.update_pet_info()
        api.update_pet_status()
        api.update_flap_status()
        # api.update_router_status()
        # api.update_timelines()

        api.set_curfew()
