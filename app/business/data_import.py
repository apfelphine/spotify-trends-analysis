import asyncio
import datetime
import json
import logging
import re
import time
from typing import Callable, Awaitable

import kagglehub
import pandas as pd
import requests
from geoalchemy2.shape import from_shape
from playwright.async_api import async_playwright
from shapely.geometry import shape
from sqlalchemy import func

from sqlmodel import Session, select

from app.database import engine
from app.models.albums import Album
from app.models.artists import Artist
from app.models.countries import Country
from app.models.tracks import Track
from app.models.trends import TrendEntry


async def import_songs_from_kaggle():
    path = kagglehub.dataset_download("asaniczka/top-spotify-songs-in-73-countries-daily-updated")
    await load_songs_from_csv(path + '/universal_top_spotify_songs.csv')


async def get_min_max_date():
    with Session(engine) as session:
        from_date = session.exec(select(func.min(TrendEntry.date))).first()
        to_date = session.exec(select(func.max(TrendEntry.date))).first()
        return {"from": from_date, "to": to_date}


async def load_songs_from_csv(path: str):
    df = pd.read_csv(
        path,
        parse_dates=['snapshot_date', 'album_release_date']
    )
    # Drop global entries (country is part of the primary key and must be given!)
    df.dropna(subset=['country'], inplace=True)

    # Delta-load
    max_date = (await get_min_max_date()).get("to", None)
    if max_date is not None:
        df = df.loc[(df['snapshot_date'] > max_date)]

    if len(df) == 0:
        print("No new data found. Skipping import...")
        return None, None

    date = df["snapshot_date"].min()
    while date <= df["snapshot_date"].max():
        next_date = date + datetime.timedelta(days=1)
        temp_df = df.loc[(df['snapshot_date'] < next_date)]
        temp_df = temp_df.loc[(temp_df['snapshot_date'] >= date)]
        print(f"Loading trends for {date} ({len(temp_df)} entries)...")
        await load_dataframe(temp_df)
        date = next_date

    print("Finished.")
    return df["snapshot_date"].min(), df["snapshot_date"].max()


async def load_dataframe(df: pd.DataFrame):
    if len(df) == 0:
        return

    with Session(engine) as session:
        await ensure_tracks_exist(df["spotify_id"].unique(), session)

        existing_track_ids: list[str] = list(session.exec(select(Track.id).distinct()).all())
        keys = set()

        for row in df.to_dict('records'):
            track_id = row["spotify_id"]
            key = (row["snapshot_date"], row["country"], row["daily_rank"])
            if track_id in existing_track_ids and key not in keys:
                session.add(
                    TrendEntry(
                        track_id=track_id,
                        date=row["snapshot_date"],
                        popularity_at_date=row["popularity"],
                        country_code=row["country"],
                        rank=row["daily_rank"],
                        **row
                    )
                )
                keys.add(key)

        session.commit()


async def get_access_token() -> str:
    # Copied from: https://www.kaggle.com/code/asaniczka/top-spotify-playlist-extractor/notebook
    url = "https://open.spotify.com/playlist/37i9dQZEVXbNG2KDcFcKOF"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        async with page.expect_request(
                re.compile("pathfinder/v1/query")
        ) as request_info:
            await page.goto(url)

        res = await request_info.value
        auth_token = await res.header_value("authorization")
        return auth_token.replace("Bearer", "").strip()


async def ensure_tracks_exist(track_ids: list[str], session: Session):
    access_token = await get_access_token()

    existing_track_ids: list[str] = list(session.exec(select(Track.id).distinct()).all())
    new_track_ids = [track_id for track_id in track_ids if track_id not in existing_track_ids]
    if len(new_track_ids) == 0:
        return

    resolved_new_tracks = await batch_spotify_request(
        new_track_ids, get_tracks_from_spotify, 100, access_token
    )

    resolved_audio_features = {feat["id"]: feat for feat in await batch_spotify_request(
        new_track_ids, get_audio_features_from_spotify, 100, access_token
    )}

    existing_album_ids: list[str] = list(session.exec(select(Album.id).distinct()).all())
    new_albums = list(
        {t["album"]["id"]: t["album"] for t in resolved_new_tracks if t["album"]["id"] not in existing_album_ids}
        .values()
    )

    existing_artist_ids: list[str] = list(session.exec(select(Artist.id).distinct()).all())
    new_artists_album_ids = {artist['id'] for album in new_albums for artist in album["artists"] if
                             artist['id'] not in existing_artist_ids}
    resolved_album_artists = await batch_spotify_request(
        list(new_artists_album_ids), get_artists_from_spotify, 10, access_token
    )

    add_artists_to_session(resolved_album_artists, session)
    add_albums_to_session(new_albums, session)

    new_track_artists_ids = {
        artist['id'] for t in resolved_new_tracks for artist in t["artists"]
        if artist["id"] not in existing_artist_ids and artist["id"] not in new_artists_album_ids
    }
    resolved_track_artists = await batch_spotify_request(
        list(new_track_artists_ids), get_artists_from_spotify, 10, access_token
    )

    add_artists_to_session(resolved_track_artists, session)
    add_tracks_to_session(resolved_new_tracks, resolved_audio_features, session)


def add_tracks_to_session(tracks: list[dict], audio_features_dict: dict, session: Session):
    for track in tracks:
        artists = track.pop('artists', [])
        album = track.pop('album', {})

        audio_features = audio_features_dict.get(track["id"])
        del audio_features["id"]
        del audio_features["type"]
        del audio_features["uri"]
        del track["duration_ms"]

        session.add(
            Track(
                album_id=album["id"],
                spotify_url=track["external_urls"]["spotify"],
                artists=[session.get(Artist, artist["id"]) for artist in artists],
                **track,
                **audio_features
            )
        )


def add_artists_to_session(artists: list[dict], session: Session):
    for artist in artists:
        session.add(
            Artist(
                image_url=artist["images"][0]["url"] if len(artist["images"]) > 0 else None,
                spotify_url=artist["external_urls"]["spotify"],
                **artist
            )
        )


def add_albums_to_session(albums: list[dict], session: Session):
    for album in albums:
        artists = album.pop('artists', [])
        session.add(
            Album(
                image_url=album["images"][0]["url"] if len(album["images"]) > 0 else None,
                spotify_url=album["external_urls"]["spotify"],
                artists=[session.get(Artist, artist["id"]) for artist in artists],
                **album
            )
        )


async def batch_spotify_request(
    ids: list[str], func: Callable[[list[str], str], Awaitable[list[dict]]], batch_size: int, access_token: str
):
    futures = []
    for i in range(0, len(ids), batch_size):
        futures.append(func(list(ids)[i:i + batch_size], access_token))

    return [
        r for response in (await asyncio.gather(*futures))
        for r in response if r is not None
    ]


async def get_tracks_from_spotify(track_ids: list[str], access_token: str) -> list[dict]:
    return (await make_spotify_request(
        "GET",
        "tracks",
        {"ids": ",".join(track_ids)},
        access_token=access_token
    )).get("tracks", [])


async def get_artists_from_spotify(artist_ids: list[str], access_token: str) -> list[dict]:
    return (await make_spotify_request(
        "GET",
        "artists",
        {"ids": ",".join(artist_ids)},
        access_token=access_token
    )).get("artists", [])


async def get_audio_features_from_spotify(track_ids: list[str], access_token: str) -> list[dict]:
    return (await make_spotify_request(
        "GET",
        "audio-features",
        {"ids": ",".join(track_ids)},
        access_token=access_token
    )).get("audio_features", [])


async def make_spotify_request(method, path, params, access_token) -> dict | list[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    retries = 0
    while retries < 5:
        response = requests.request(
            method,
            "https://api.spotify.com/v1/" + path,
            headers=headers,
            params=params
        )
        try:
            response.raise_for_status()
            return response.json()
        except Exception:
            print(
                f"Got an error attempting {method} on {path}: "
                f"{response.text} [{response.status_code}]"
            )

            if response.status_code == 401:
                # Refresh the access token
                access_token = await get_access_token()
                headers = {"Authorization": f"Bearer {access_token}"}

            retries += 1
            time.sleep(10 * retries)
            logging.info(f"Retrying...")
    else:
        raise Exception(f"Failed {method} on {path}")


def import_countries():
    with Session(engine) as session:
        print("Importing country data...")
        imported_countries = []
        with open('static/world-administrative-boundaries.geojson') as file:
            gj = json.load(file)
            for feature in gj['features']:
                alpha_2_code = feature['properties']['iso_3166_1_alpha_2_codes']
                if not alpha_2_code or session.get(Country, alpha_2_code) is not None:
                    continue

                name = feature['properties']['name']
                print(alpha_2_code, end='...')
                imported_countries.append(alpha_2_code)
                session.add(
                    Country(
                        alpha_2_code=alpha_2_code,
                        name=name,
                        polygon=from_shape(
                            shape(feature['geometry'])
                        )
                    )
                )
        session.commit()
        if len(imported_countries) > 0:
            print(f"\nFinished importing {len(imported_countries)} countries...")
        print("Already imported country data.")
