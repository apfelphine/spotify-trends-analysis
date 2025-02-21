from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from app.models.albums import Album
from app.models.artists import Artist
from app.models.links import TrackArtistLink

if TYPE_CHECKING:
    from app.models.trends import TrendEntry


class Track(SQLModel, table=True):
    __tablename__ = "tracks"

    id: str = Field(primary_key=True)
    name: str
    preview_url: Optional[str]
    spotify_url: str

    # Metadata
    explicit: bool
    duration_ms: int
    danceability: float
    energy: float
    key: int
    loudness: float
    speechiness: float
    acousticness: float
    instrumentalness: float
    valence: float
    tempo: float
    liveness: float
    mode: int
    time_signature: int

    # Foreign keys / relations
    album_id: str = Field(foreign_key="albums.id")
    album: Album = Relationship(back_populates="tracks")
    artists: list[Artist] = Relationship(back_populates="tracks", link_model=TrackArtistLink)
    trend_entries: list["TrendEntry"] = Relationship(back_populates="track", cascade_delete=True)

