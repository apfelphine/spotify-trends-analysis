import datetime
from typing import Optional

from fastapi import APIRouter
from app.business.maps import get_map_with_features
from app.business.popularity import calculate_artist_popularity, calculate_track_popularity, calculate_album_popularity
from app.business.trends import get_most_popular_album_for_country, get_for_all_countries, \
    get_most_popular_track_for_country, get_most_popular_artist_for_country
from app.models.maps import FeatureCollection

router = APIRouter(
    tags=["map"],
    prefix="/maps",
)


@router.get("/popularity/artist/{artist_id}")
async def get_artist_popularity_map(
    artist_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> FeatureCollection:
    """Geo geojson with artist popularity"""
    return await get_map_with_features(
        await calculate_artist_popularity(artist_id, from_date, to_date),
        feature_key="popularity"
    )


@router.get("/popularity/track/{track_id}")
async def get_track_popularity_map(
    track_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> FeatureCollection:
    """Geo geojson with track popularity"""
    return await get_map_with_features(
        await calculate_track_popularity(track_id, from_date, to_date),
        feature_key="popularity"
    )


@router.get("/popularity/album/{album_id}")
async def get_album_popularity_map(
    album_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> FeatureCollection:
    """Geo geojson with album popularity"""
    return await get_map_with_features(
        await calculate_album_popularity(album_id, from_date, to_date),
        feature_key="popularity"
    )


@router.get("/trends/artist")
async def get_artist_trend_map(
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> FeatureCollection:
    """Geo geojson with artist trends"""
    return await get_map_with_features(
        get_for_all_countries(get_most_popular_artist_for_country, from_date, to_date),
        feature_key="artist"
    )


@router.get("/trends/track")
async def get_track_trend_map(
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> FeatureCollection:
    """Geo geojson with track trends"""
    return await get_map_with_features(
        get_for_all_countries(get_most_popular_track_for_country, from_date, to_date),
        feature_key="track"
    )


@router.get("/trends/album")
async def get_album_trend_map(
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> FeatureCollection:
    """Geo geojson with album trends"""
    return await get_map_with_features(
        get_for_all_countries(get_most_popular_album_for_country, from_date, to_date),
        feature_key="album"
    )
