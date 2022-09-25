import datetime

import pytest
from astral import location

from sureflap_gcloud import get_curfew_times, get_astral_location, CurfewTimes


@pytest.fixture
def location_akl() -> location.Location:
    return get_astral_location("Auckland,New Zealand,Pacific/Auckland,36°55'S,174°50'E")


@pytest.mark.freeze_time("2022-09-24T05:00:00+12:00")
def test_before_start_dst_nz(location_akl):
    assert get_curfew_times(location_akl) == CurfewTimes(
        lock_time=datetime.time(18, 18),
        unlock_time=datetime.time(6, 8),
    )


@pytest.mark.freeze_time("2022-09-25T05:00:00+13:00")
def test_after_start_dst_nz(location_akl):
    assert get_curfew_times(location_akl) == CurfewTimes(
        lock_time=datetime.time(19, 18),
        unlock_time=datetime.time(7, 6),
    )
