from fastapi import APIRouter, Depends

from app.api._utils import DateRange
from app.business.maps import get_map_with_features
from app.business.popularity import calculate_artist_popularity, calculate_track_popularity, calculate_album_popularity
from app.business.trends import get_most_popular_track_per_country, \
    get_most_popular_album_per_country, get_most_popular_artist_per_country
from app.models.maps import FeatureCollection

router = APIRouter(
    tags=["map"],
    prefix="/maps",
)


@router.get("/popularity/artist/{artist_id}")
async def get_artist_popularity_map(
    artist_id: str,
    date_range: DateRange = Depends()
) -> FeatureCollection:
    """Geo geojson with artist popularity"""
    return await get_map_with_features(
        await calculate_artist_popularity(artist_id, date_range.from_date, date_range.to_date),
        feature_key="popularity"
    )


@router.get("/popularity/track/{track_id}")
async def get_track_popularity_map(
    track_id: str,
    date_range: DateRange = Depends()
) -> FeatureCollection:
    """Geo geojson with track popularity"""
    return await get_map_with_features(
        await calculate_track_popularity(track_id, date_range.from_date, date_range.to_date),
        feature_key="popularity"
    )


@router.get("/popularity/album/{album_id}")
async def get_album_popularity_map(
    album_id: str,
    date_range: DateRange = Depends()
) -> FeatureCollection:
    """Geo geojson with album popularity"""
    return await get_map_with_features(
        await calculate_album_popularity(album_id, date_range.from_date, date_range.to_date),
        feature_key="popularity"
    )


@router.get("/trends/artist")
async def get_artist_trend_map(
    date_range: DateRange = Depends()
) -> FeatureCollection:
    """Geo geojson with artist trends"""
    return await get_map_with_features(
        get_most_popular_artist_per_country(date_range.from_date, date_range.to_date),
        feature_key="artist"
    )


@router.get("/trends/track")
async def get_track_trend_map(
    date_range: DateRange = Depends()
) -> FeatureCollection:
    """Geo geojson with track trends"""
    return await get_map_with_features(
        get_most_popular_track_per_country(date_range.from_date, date_range.to_date),
        feature_key="track"
    )


@router.get("/trends/album")
async def get_album_trend_map(
    date_range: DateRange = Depends()
) -> FeatureCollection:
    """Geo geojson with album trends"""
    return await get_map_with_features(
        get_most_popular_album_per_country(date_range.from_date, date_range.to_date),
        feature_key="album"
    )
