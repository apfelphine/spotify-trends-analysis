from typing import List, Optional, Any

from pydantic import BaseModel

from app.models.albums import AlbumPublicWithArtists
from app.models.artists import Artist
from app.models.tracks import TrackPublicWithAlbumAndArtists


class Properties(BaseModel):
    alpha_2_code: str
    name: str
    track: Optional[TrackPublicWithAlbumAndArtists] = None
    artist: Optional[Artist] = None
    album: Optional[AlbumPublicWithArtists] = None
    popularity: Optional[float] = None


class Feature(BaseModel):
    type: str = "Feature"
    properties: Properties
    geometry: Any
    id: Optional[Any] = None


class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[Feature]
