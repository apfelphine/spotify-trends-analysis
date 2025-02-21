import datetime
from typing import Optional, Callable, Any

from sqlmodel import Session, select

from app.database import engine
from app.models.albums import Album
from app.models.artists import Artist
from app.models.tracks import Track
from app.models.trends import TrendEntry

# print(get_for_all_countries(get_most_popular_artist_for_country))


def get_for_all_countries(
    func: Callable[[str, Optional[datetime.datetime], Optional[datetime.datetime]], Any],
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
):
    with Session(engine) as session:
        all_countries = list(session.exec(select(TrendEntry.country_code).distinct()).all())
        print(all_countries)

    res = {}
    for country in all_countries:
        res[country] = func(country, from_date, to_date)
    return res


def get_most_popular_track_for_country(
    country_code: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> Track:
    with Session(engine) as session:
        trends = _get_trend_entries(session, country_code, from_date, to_date)

        tracks = {}
        for trend in trends:
            ranks = [trend.rank]
            if trend.track_id in tracks:
                ranks += tracks[trend.track_id]
            tracks[trend.track_id] = ranks

        sorted_tracks = sorted(tracks.items(), key=lambda x: _score(x[1], len(trends)))
        return session.get(Track, sorted_tracks[0][0])  # noqa


def get_most_popular_album_for_country(
    country_code: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> Track:
    with Session(engine) as session:
        trends = _get_trend_entries(session, country_code, from_date, to_date)

        albums = {}
        for trend in trends:
            ranks = [trend.rank]
            if trend.track.album_id in albums:
                ranks += albums[trend.track.album_id]
            albums[trend.track.album_id] = ranks

        sorted_albums = sorted(albums.items(), key=lambda x: _score(x[1], len(trends)))
        return session.get(Album, sorted_albums[0][0]) # noqa


def get_most_popular_artist_for_country(
    country_code: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> Track:
    with Session(engine) as session:
        trends = _get_trend_entries(session, country_code, from_date, to_date)

        artists = {}
        for trend in trends:

            for artist in trend.track.artists:
                ranks = [trend.rank]
                if artist.id in artists:
                    ranks += artists[artist.id]
                artists[artist.id] = ranks

        sorted_artists = sorted(artists.items(), key=lambda x: _score(x[1], len(trends)))
        return session.get(Artist, sorted_artists[0][0]) # noqa


def _get_trend_entries(
    session: Session,
    country_code: str,
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> list[TrendEntry]:
    statement = select(TrendEntry).where(TrendEntry.country_code == country_code)
    if from_date is not None:
        statement = statement.where(TrendEntry.date >= from_date)
    if to_date is not None:
        statement = statement.where(TrendEntry.date <= to_date)
    return list(session.exec(statement).all())


def _score(ranks: list[int], num_days: int):
    return (sum(ranks) + ((num_days - len(ranks)) * 51)) / num_days
