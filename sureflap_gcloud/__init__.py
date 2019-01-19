import datetime
import hashlib
import os
import pickle

import pytz
from google.cloud import firestore
import sure_petcare


class SurePetFlapFireBaseCache(sure_petcare.SurePetFlap):
    """
    Override SurePetFlapAPI's cache load/save,
    to store in Google Firestore instead of on disk
    """

    # TODO
    DOC_ID = "1"

    def __init__(self, *args, **kwargs):
        self.db = firestore.Client()

        super().__init__(*args, **kwargs)

    def get_tz(self, household_id=None):
        household_id = household_id or self.default_household

        return pytz.timezone(self.households[household_id]["olson_tz"])

    def get_current_status_dict(self, pet_id, household_id=None):
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

    def get_firebase_doc_ref(self):
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

    def get_dict_for_firebase(self):
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
            "pet_statuses": pet_statuses,
        }

    def __exit__(self, *args, **kwargs):
        # TODO - copy cache locking behaviour?
        super().__exit__(*args, **kwargs)

        self.__read_only = True

        doc_ref = self.get_firebase_doc_ref()
        doc_ref.set(self.get_dict_for_firebase())


def gen_device_id_from_bytes(b):
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
        api.update()
