import datetime
from typing import Optional

from sqlmodel import Session, select
from sqlalchemy import func

from app.business.utils import add_date_filter
from app.database import engine
from app.models.albums import Album, AlbumPublicWithArtists
from app.models.artists import Artist
from app.models.links import TrackArtistLink
from app.models.tracks import Track, TrackPublicWithAlbumAndArtists
from app.models.trends import TrendEntry


def get_most_popular_track_per_country(
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
) -> dict[str, TrackPublicWithAlbumAndArtists]:
    statement = (
        select(
            TrendEntry.country_code,
            TrendEntry.track_id,
            func.sum(51 - TrendEntry.rank).label("total_score"))
        .group_by(TrendEntry.track_id, TrendEntry.country_code)
        .order_by(TrendEntry.country_code, func.sum(51 - TrendEntry.rank).desc())
    )

    statement = add_date_filter(statement, from_date, to_date)

    with Session(engine) as session:
        res = session.execute(statement).all()

        country_tracks = {}

        for r in res:
            if r[0] in country_tracks:
                continue
            else:
                country_tracks[r[0]] = session.get(Track, r[1])

        return country_tracks  # noqa


def get_most_popular_album_per_country(
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
) -> dict[str, AlbumPublicWithArtists]:
    statement = (
        select(
            TrendEntry.country_code,
            Track.album_id,
            func.sum(51 - TrendEntry.rank).label("total_score"))
        .where(TrendEntry.track_id == Track.id)
        .group_by(Track.album_id, TrendEntry.country_code)
        .order_by(TrendEntry.country_code, func.sum(51 - TrendEntry.rank).desc())
    )

    statement = add_date_filter(statement, from_date, to_date)

    with Session(engine) as session:
        res = session.execute(statement).all()

        country_albums = {}

        for r in res:
            if r[0] in country_albums:
                continue
            else:
                country_albums[r[0]] = session.get(Album, r[1])

        return country_albums  # noqa


def get_most_popular_artist_per_country(
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
) -> dict[str, Artist]:
    statement = (
        select(
            TrendEntry.country_code,
            TrackArtistLink.artist_id,
            func.sum(51 - TrendEntry.rank).label("total_score"))
        .where(TrendEntry.track_id == TrackArtistLink.track_id)
        .group_by(TrackArtistLink.artist_id, TrendEntry.country_code)
        .order_by(TrendEntry.country_code, func.sum(51 - TrendEntry.rank).desc())
    )

    statement = add_date_filter(statement, from_date, to_date)

    with Session(engine) as session:
        res = session.execute(statement).all()

        country_artists = {}

        for r in res:
            if r[0] in country_artists:
                continue
            else:
                country_artists[r[0]] = session.get(Artist, r[1])

        return country_artists  # noqa


def get_most_popular_track_for_country(
        country_code: str,
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
) -> TrackPublicWithAlbumAndArtists:
    with Session(engine) as session:
        trends = _get_trend_entries(session, country_code, from_date, to_date)

        tracks = {}
        for trend in trends:
            ranks = [trend.rank]
            if trend.track_id in tracks:
                ranks += tracks[trend.track_id]
            tracks[trend.track_id] = ranks

        sorted_tracks = sorted(tracks.items(), key=lambda x: _score(x[1], len(trends)), reverse=True)
        return session.get(Track, sorted_tracks[0][0])  # noqa


def get_most_popular_album_for_country(
        country_code: str,
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
) -> AlbumPublicWithArtists:
    with Session(engine) as session:
        trends = _get_trend_entries(session, country_code, from_date, to_date)

        albums = {}
        for trend in trends:
            ranks = [trend.rank]
            if trend.track.album_id in albums:
                ranks += albums[trend.track.album_id]
            albums[trend.track.album_id] = ranks

        sorted_albums = sorted(albums.items(), key=lambda x: _score(x[1], len(trends)), reverse=True)
        return session.get(Album, sorted_albums[0][0])  # noqa


def get_most_popular_artist_for_country(
        country_code: str,
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
) -> Artist:
    with Session(engine) as session:
        trends = _get_trend_entries(session, country_code, from_date, to_date)

        artists = {}
        for trend in trends:

            for artist in trend.track.artists:
                ranks = [trend.rank]
                if artist.id in artists:
                    ranks += artists[artist.id]
                artists[artist.id] = ranks

        sorted_artists = sorted(artists.items(), key=lambda x: _score(x[1], len(trends)), reverse=True)
        return session.get(Artist, sorted_artists[0][0])  # noqa


def _get_trend_entries(
        session: Session,
        country_code: Optional[str] = None,
        from_date: Optional[datetime.datetime] = None,
        to_date: Optional[datetime.datetime] = None,
) -> list[TrendEntry]:
    statement = select(TrendEntry)
    if country_code is not None:
        statement = statement.where(TrendEntry.country_code == country_code)
    statement = add_date_filter(statement, from_date, to_date)
    return list(session.exec(statement).all())


def _score(ranks: list[int], num_days: int):
    return (sum([51 - r for r in ranks])) / num_days
