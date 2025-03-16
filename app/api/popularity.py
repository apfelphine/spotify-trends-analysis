from fastapi import APIRouter, Depends

from app.api._utils import DateRange
from app.business.popularity import calculate_track_popularity, calculate_album_popularity, calculate_artist_popularity

router = APIRouter(
    tags=["popularity"],
    prefix="/popularity",
)


@router.get("/album/{album_id}")
async def get_album_popularity(
    album_id: str,
    date_range: DateRange = Depends()
) -> dict[str, float]:
    """Calculate the popularity of a specific album across the world in a specific range"""
    return await calculate_album_popularity(album_id, date_range.from_date, date_range.to_date)


@router.get("/artist/{artist_id}")
async def get_artist_popularity(
    artist_id: str,
    date_range: DateRange = Depends()
) -> dict[str, float]:
    """Calculate the popularity of a specific artist across the world in a specific range"""
    return await calculate_artist_popularity(artist_id, date_range.from_date, date_range.to_date)


@router.get("/track/{track_id}")
async def get_track_popularity(
    track_id: str,
    date_range: DateRange = Depends()
) -> dict[str, float]:
    """Calculate the popularity of a specific track across the world in a specific range"""
    return await calculate_track_popularity(track_id, date_range.from_date, date_range.to_date)

