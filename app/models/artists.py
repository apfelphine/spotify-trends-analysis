from typing import List, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, Relationship

from app.models.links import AlbumArtistLink, TrackArtistLink


class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: str = Field(primary_key=True)
    name: str
    image_url: Optional[str]
    spotify_url: str
    genres: List[str] = Field(sa_column=Column(JSON))

    tracks: list["Track"] = Relationship(back_populates="artists", link_model=TrackArtistLink)
    albums: list["Album"] = Relationship(back_populates="artists", link_model=AlbumArtistLink)

    class Config:
        arbitrary_types_allowed = True  # Needed for Column(JSON)
