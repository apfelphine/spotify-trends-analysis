from fastapi import APIRouter, Depends

from app.api._utils import DateRange
from app.business.trends import get_most_popular_artist_for_country, \
    get_most_popular_track_for_country, get_most_popular_album_for_country, get_most_popular_album_per_country, \
    get_most_popular_track_per_country, get_most_popular_artist_per_country
from app.models.albums import AlbumPublicWithArtists
from app.models.artists import Artist
from app.models.tracks import TrackPublicWithAlbumAndArtists

router = APIRouter(
    tags=["trends"],
    prefix="/trends",
)


@router.get("/album")
async def get_most_popular_album(
    date_range: DateRange = Depends()
) -> dict[str, AlbumPublicWithArtists]:
    """Retrieve the most popular album in all available countries in a specific time range"""
    return get_most_popular_album_per_country(date_range.from_date, date_range.to_date)


@router.get("/album/{country_code}")
async def get_most_popular_album_in_country(
    country_code: str,
    date_range: DateRange = Depends()
) -> AlbumPublicWithArtists:
    """Retrieve the most popular album in a specific country in a specific time range"""
    return get_most_popular_album_for_country(country_code, date_range.from_date, date_range.to_date)


@router.get("/artist")
async def get_most_popular_artist(
    date_range: DateRange = Depends()
) -> dict[str, Artist]:
    """Retrieve the most popular artist in all available countries in a specific time range"""
    return get_most_popular_artist_per_country(date_range.from_date, date_range.to_date)


@router.get("/artist/{country_code}")
async def get_most_popular_artist_in_country(
    country_code: str,
    date_range: DateRange = Depends()
) -> Artist:
    """Retrieve the most popular artist in a specific country in a specific time range"""
    return get_most_popular_artist_for_country(country_code, date_range.from_date, date_range.to_date)


@router.get("/track")
async def get_most_popular_track(
    date_range: DateRange = Depends()
) -> dict[str, TrackPublicWithAlbumAndArtists]:
    """Retrieve the most popular track in all available countries in a specific time range"""
    return get_most_popular_track_per_country(date_range.from_date, date_range.to_date)


@router.get("/track/{country_code}")
async def get_most_popular_track_in_country(
    country_code: str,
    date_range: DateRange = Depends()
) -> TrackPublicWithAlbumAndArtists:
    """Retrieve the most popular track in a specific country in a specific time range"""
    return get_most_popular_track_for_country(country_code, date_range.from_date, date_range.to_date)

