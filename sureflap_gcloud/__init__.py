import asyncio
import datetime
import logging
import os
from typing import cast

from astral import LocationInfo
from astral.location import Location

from surepy import Flap, Surepy

logger = logging.getLogger(__name__)


def set_curfew():
    try:
        location_tuple = os.environ["ASTRAL_LOCATION"].split(",")
    except KeyError:
        logger.error(
            "Expected ASTRAL_LOCATION as a comma separated string in the format of Astral's LocationInfo, "
            """eg: ASTRAL_LOCATION="Auckland,New Zealand,Pacific/Auckland,36°55'S,174°50'E" """
        )
        location_tuple = []

    location = Location(LocationInfo(*location_tuple))
    sun_times = location.sun(local=True)

    asyncio.run(
        _set_curfew(
            device_id=int(os.environ["DEVICE_ID"]),
            token=os.environ["SUREPY_AUTH_TOKEN"],
            lock_time=sun_times["sunset"].time(),
            unlock_time=sun_times["sunrise"].time(),
        )
    )


async def _set_curfew(
    *, device_id: int, token: str, lock_time: datetime.time, unlock_time: datetime.time
):

    sp = Surepy(auth_token=token)

    if (flap := await sp.get_device(device_id=device_id)) and (type(flap) == Flap):
        flap = cast(Flap, flap)

        logger.info(
            f"setting %s curfew lock_time=%s unlock_time=%s",
            flap.name,
            lock_time,
            unlock_time,
        )

        if await sp.sac.set_curfew(
            device_id=device_id, lock_time=lock_time, unlock_time=unlock_time
        ):
            logger.info("set_curfew success")
        else:
            logger.error("set_curfew may have failed, unexpected response")
