import datetime
from typing import List

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


# class AudioFeatures(SQLModel):
#     danceability: float
#     energy: float
#     key: int
#     loudness: float
#     speechiness: float
#     acousticness: float
#     instrumentalness: float
#     valence: float
#     tempo: float
#     liveness: float
#     mode: int


class Track(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    artists: List[str] = Field(sa_column=Column(JSON))  # todo: use spotify web api to get artist details for track id
    album_name: str  # todo: use spotify web api to get album details for track id
    album_release_date: datetime.datetime  # todo: use spotify web api to get album details for track id

    # Metadata
    explicit: bool
    duration_ms: int
    popularity: int

    # audio_features: AudioFeatures

    class Config:
        arbitrary_types_allowed = True  # Needed for Column(JSON)
