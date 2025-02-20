import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from app.models.tracks import Track


class TrendEntry(SQLModel, table=True):
    __tablename__ = 'trend_entries'

    date: datetime.datetime = Field(primary_key=True)
    country_code: str = Field(primary_key=True)
    rank: int = Field(ge=1, le=50, primary_key=True)

    daily_movement: int = Field(ge=-49, le=49)
    weekly_movement: int = Field(ge=-49, le=49)

    popularity_at_date: int = Field(ge=0, le=100)

    track_id: str = Field(foreign_key="tracks.id")
    track: Track = Relationship(back_populates="trend_entries")

