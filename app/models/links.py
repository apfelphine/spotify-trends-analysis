from sqlmodel import SQLModel, Field


class AlbumArtistLink(SQLModel, table=True):
    album_id: str = Field(foreign_key="albums.id", primary_key=True)
    artist_id: str = Field(foreign_key="artists.id", primary_key=True)


class TrackArtistLink(SQLModel, table=True):
    track_id: str = Field(foreign_key="tracks.id", primary_key=True)
    artist_id: str = Field(foreign_key="artists.id", primary_key=True)
