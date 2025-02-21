import enum
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from app.models.links import AlbumArtistLink


class AlbumType(str, enum.Enum):
    ALBUM = "album"
    SINGLE = "single"
    COMPILATION = "compilation"


class Album(SQLModel, table=True):
    __tablename__ = "albums"

    id: str = Field(primary_key=True)
    name: str
    total_tracks: int

    album_type: AlbumType
    image_url: Optional[str]
    spotify_url: str

    artists: list["Artist"] = Relationship(back_populates="albums", link_model=AlbumArtistLink)
    tracks: list["Track"] = Relationship(back_populates="album", cascade_delete=True)
