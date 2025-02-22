import datetime
from typing import Optional

from fastapi import APIRouter

from app.business.trends import get_for_all_countries, get_most_popular_artist_for_country, \
    get_most_popular_track_for_country, get_most_popular_album_for_country
from app.models.albums import Album
from app.models.artists import Artist
from app.models.tracks import Track

router = APIRouter(
    tags=["trends"],
    prefix="/trends",
)


@router.get("/album")
async def get_most_popular_album(
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, Album]:
    """Retrieve the most popular album in all available countries in a specific time range"""
    return get_for_all_countries(get_most_popular_album_for_country, from_date, to_date)


@router.get("/album/{country_code}")
async def get_most_popular_album_in_country(
    country_code: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> Album:
    """Retrieve the most popular album in a specific country in a specific time range"""
    return get_most_popular_album_for_country(country_code, from_date, to_date)


@router.get("/artist")
async def get_most_popular_artist(
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, Artist]:
    """Retrieve the most popular artist in all available countries in a specific time range"""
    return get_for_all_countries(get_most_popular_artist_for_country, from_date, to_date)


@router.get("/artist/{country_code}")
async def get_most_popular_artist_in_country(
    country_code: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> Artist:
    """Retrieve the most popular artist in a specific country in a specific time range"""
    return get_most_popular_artist_for_country(country_code, from_date, to_date)


@router.get("/track")
async def get_most_popular_track(
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, Track]:
    """Retrieve the most popular track in all available countries in a specific time range"""
    return get_for_all_countries(get_most_popular_track_for_country, from_date, to_date)


@router.get("/track/{country_code}")
async def get_most_popular_track(
    country_code: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> Track:
    """Retrieve the most popular track in a specific country in a specific time range"""
    return get_most_popular_track_for_country(country_code, from_date, to_date)

