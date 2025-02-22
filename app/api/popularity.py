import datetime
from typing import Optional

from fastapi import APIRouter

from app.business.popularity import calculate_track_popularity, calculate_album_popularity, calculate_artist_popularity

router = APIRouter(
    tags=["popularity"],
    prefix="/popularity",
)


@router.get("/album/{album_id}")
async def get_album_popularity(
    album_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, float]:
    """Calculate the popularity of a specific album across the world in a specific range"""
    return calculate_album_popularity(album_id, from_date, to_date)


@router.get("/artist/{artist_id}")
async def get_artist_popularity(
    artist_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, float]:
    """Calculate the popularity of a specific artist across the world in a specific range"""
    return calculate_artist_popularity(artist_id, from_date, to_date)


@router.get("/track/{track_id}")
async def get_track_popularity(
    track_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, float]:
    """Calculate the popularity of a specific track across the world in a specific range"""
    return calculate_track_popularity(track_id, from_date, to_date)

