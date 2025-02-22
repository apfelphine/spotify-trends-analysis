import datetime
from typing import Optional

from sqlmodel import Session, select, or_

from app.business.countries import get_all_countries
from app.database import engine
from app.models.albums import Album
from app.models.artists import Artist
from app.models.exceptions import NotFoundException
from app.models.tracks import Track
from app.models.trends import TrendEntry


def calculate_artist_popularity(
    artist_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
):
    with (Session(engine) as session):
        artist = session.get(Artist, artist_id)
        if not artist:
            raise NotFoundException(f"There is no artist with ID {artist_id}.")
        where_filter = or_(*[TrendEntry.track_id == track.id for track in artist.tracks])
        return _calculate_popularity(session, where_filter, from_date, to_date)


def calculate_track_popularity(
    track_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, float]:
    with (Session(engine) as session):
        if not session.get(Track, track_id):
            raise NotFoundException(f"There is no track with ID {track_id}.")
        where_filter = TrendEntry.track_id == track_id
        return _calculate_popularity(session, where_filter, from_date, to_date)


def calculate_album_popularity(
    album_id: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, float]:
    with (Session(engine) as session):
        album = session.get(Album, album_id)
        if not album:
            raise NotFoundException(f"There is no album with ID {album_id}.")
        where_filter = or_(*[TrendEntry.track_id == track.id for track in album.tracks])
        return _calculate_popularity(session, where_filter, from_date, to_date)


def _calculate_popularity(
    session: Session,
    where_filter,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
):
    all_countries = get_all_countries(from_date, to_date)
    country_scores = {}

    for country_code in all_countries:
        statement = select(TrendEntry).where(TrendEntry.country_code == country_code).where(
            where_filter
        )
        if from_date is not None:
            statement = statement.where(TrendEntry.date >= from_date)
        if to_date is not None:
            statement = statement.where(TrendEntry.date <= to_date)
        trends = list(session.exec(statement).all())
        country_scores[country_code] = sum([51 - t.rank for t in trends])

    max_score = max(country_scores.values())
    return {country_code: score / max_score for country_code, score in country_scores.items()}