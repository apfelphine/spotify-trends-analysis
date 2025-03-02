import datetime
from typing import Optional, Callable

from sqlmodel import Session, select

from app.business.countries import get_all_countries
from app.database import engine
from app.models.albums import Album, AlbumPublicWithArtists
from app.models.artists import Artist
from app.models.tracks import Track, TrackPublicWithAlbumAndArtists
from app.models.trends import TrendEntry


def get_for_all_countries(
    func: Callable[[str, Optional[datetime.datetime], Optional[datetime.datetime]], Artist | TrackPublicWithAlbumAndArtists | AlbumPublicWithArtists],
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> dict[str, Artist | TrackPublicWithAlbumAndArtists | AlbumPublicWithArtists]:
    res = {}
    for country in get_all_countries(from_date, to_date):
        res[country] = func(country, from_date, to_date)
    return res


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
        return session.get(Album, sorted_albums[0][0]) # noqa


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
    return (sum([51 - r for r in ranks])) / num_days
