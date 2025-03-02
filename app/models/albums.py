import enum
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from app.models.links import AlbumArtistLink
from app.models.artists import Artist

if TYPE_CHECKING:
    from app.models.tracks import Track


class AlbumType(str, enum.Enum):
    ALBUM = "album"
    SINGLE = "single"
    COMPILATION = "compilation"


class AlbumBase(SQLModel):
    name: str
    total_tracks: int

    album_type: AlbumType
    image_url: Optional[str]
    spotify_url: str


class Album(AlbumBase, table=True):
    __tablename__ = "albums"

    id: str = Field(primary_key=True)
    artists: list[Artist] = Relationship(
        back_populates="albums",
        link_model=AlbumArtistLink,
        sa_relationship_kwargs=dict(lazy="joined")
    )
    tracks: list["Track"] = Relationship(back_populates="album", cascade_delete=True)


class AlbumPublic(AlbumBase):
    id: str


class AlbumPublicWithArtists(AlbumPublic):
    artists: list[Artist]

