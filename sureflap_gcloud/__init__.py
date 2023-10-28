import asyncio
import datetime
import logging
import os
from datetime import time
from typing import NamedTuple
from typing import cast

from astral import LocationInfo
from astral.location import Location

from surepy import Flap, Surepy

logger = logging.getLogger(__name__)


class CurfewTimes(NamedTuple):
    lock_time: time
    unlock_time: time


def set_curfew():
    try:
        location_env = os.environ["ASTRAL_LOCATION"]
    except KeyError:
        logger.error(
            "Expected ASTRAL_LOCATION as a comma separated string in the format of Astral's LocationInfo, "
            """eg: ASTRAL_LOCATION="Auckland,New Zealand,Pacific/Auckland,36°55'S,174°50'E" """
        )
        location_env = ""

    location = get_astral_location(location_env)
    curfew_times = get_curfew_times(location)

    asyncio.run(
        _set_curfew(
            device_id=int(os.environ["DEVICE_ID"]),
            token=os.environ["SUREPY_AUTH_TOKEN"],
            lock_time=curfew_times.lock_time,
            unlock_time=curfew_times.unlock_time,
        )
    )


def get_astral_location(location_env: str) -> Location:
    location_parts = location_env.split(",")
    return Location(LocationInfo(*location_parts))


def get_curfew_times(location: Location) -> CurfewTimes:
    sun_times = location.sun(local=True)
    return CurfewTimes(
        # round down time to the minute to reduce noise
        lock_time=sun_times["sunset"].replace(second=0, microsecond=0).time(),
        unlock_time=sun_times["sunrise"].replace(second=0, microsecond=0).time(),
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
