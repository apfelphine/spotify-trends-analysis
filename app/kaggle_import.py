import asyncio
import datetime
import logging
import math
import re
import time

import kagglehub
import pandas as pd
import requests
from playwright.async_api import async_playwright

from sqlmodel import SQLModel, Field, Session, select

from app.database import engine
from app.models.albums import Album
from app.models.artists import Artist
from app.models.tracks import Track
from app.models.trends import TrendEntry


class DataImport(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    max_imported_date: datetime.datetime
    last_imported_version: str = Field(default="")


async def import_songs_from_kaggle():
    # return
    path = kagglehub.dataset_download("asaniczka/top-spotify-songs-in-73-countries-daily-updated")
    current_version = path.split("/")[-1]

    with Session(engine) as session:
        last_import = session.get(DataImport, 1)

        if last_import is not None and last_import.last_imported_version == current_version:
            print(f"Already imported version {current_version}. Skipping import...")
            return

    await load_songs_from_csv(path + '/universal_top_spotify_songs.csv', current_version)


async def load_songs_from_csv(path: str, version: str) -> int:
    df = pd.read_csv(
        path,
        parse_dates=['snapshot_date', 'album_release_date']
    )

    with Session(engine) as session:
        last_import = session.get(DataImport, 1)
        if last_import is not None:
            df = df.loc[(df['snapshot_date'] > last_import.max_imported_date)]  # Delta-load

        # Drop global entries (country is part of the primary key and must be given!)
        df.dropna(subset=['country'], inplace=True)

        total_entries = len(df)
        if total_entries == 0:
            print("No new trend entries found...")
            return 0

        await ensure_tracks_exist(df["spotify_id"].unique())
        new_trend_entry_count = 0
        steps = math.ceil(total_entries / 10)

        print(
            f"Importing {total_entries} trend entries... "
            f"{new_trend_entry_count}/{total_entries} "
            f"({new_trend_entry_count / total_entries * 100:.0f}%)"
        )

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
                new_trend_entry_count += 1

            if new_trend_entry_count % steps == 0:
                print(
                    f"Importing {total_entries} trend entries... "
                    f"{new_trend_entry_count}/{total_entries} "
                    f"({new_trend_entry_count / total_entries * 100:.0f}%)"
                )

        if last_import is not None:
            last_import.last_imported_version = version
            last_import.max_imported_date = df["snapshot_date"].max()
        else:
            session.add(
                DataImport(
                    max_imported_date=df["snapshot_date"].max(),
                    last_imported_version=version,
                )
            )

        session.commit()

    print("Finished.")
    return new_trend_entry_count


async def get_access_token() -> str:
    # Copied from: https://www.kaggle.com/code/asaniczka/top-spotify-playlist-extractor/notebook
    logging.info("Getting an access token for the spotify api")
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


async def ensure_tracks_exist(track_ids: list[str]):
    access_token = await get_access_token()

    with Session(engine) as session:
        print(f"Ensuring all {len(track_ids)} unique tracks are added to database...")
        existing_track_ids: list[str] = list(session.exec(select(Track.id).distinct()).all())
        existing_artist_ids: list[str] = list(session.exec(select(Artist.id).distinct()).all())
        existing_album_ids: list[str] = list(session.exec(select(Album.id).distinct()).all())

        new_track_ids = [track_id for track_id in track_ids if track_id not in existing_track_ids]
        print(f"Resolving {len(new_track_ids)} new tracks...")

        track_futures = []
        feature_futures = []
        for i in range(0, len(new_track_ids), 100):
            track_futures.append(get_tracks_from_spotify(new_track_ids[i:i + 100], access_token))
            feature_futures.append(get_audio_features_from_spotify(new_track_ids[i:i + 100], access_token))

        resolved_new_tracks = [track for response in (await asyncio.gather(*track_futures)) for track in response if
                               track is not None]
        # assert len(new_track_ids) == len(resolved_new_tracks)
        print(f"Successfully retrieved {len(resolved_new_tracks)} tracks...")

        resolved_audio_features = {feat["id"]: feat for response in (await asyncio.gather(*feature_futures)) for feat in
                                   response if feat is not None}
        # assert len(new_track_ids) == len(resolved_audio_features)
        print(f"Successfully retrieved audio features for {len(resolved_audio_features)} tracks...")

        new_albums = [t["album"] for t in resolved_new_tracks if t["album"]["id"] not in existing_album_ids]
        print(f"There are {len({album['id'] for album in new_albums})} new albums...")

        new_artists_album_ids = {artist['id'] for album in new_albums for artist in album["artists"] if artist['id'] not in existing_artist_ids}
        print(f"There are {len(new_artists_album_ids)} new artists in the albums...")
        print(f"Resolving {len(new_artists_album_ids)} new artists...")
        album_artist_futures = []
        for i in range(0, len(new_artists_album_ids), 10):
            album_artist_futures.append(get_artists_from_spotify(list(new_artists_album_ids)[i:i + 10], access_token))

        resolved_album_artists = [artist for response in (await asyncio.gather(*album_artist_futures)) for artist in
                                  response if artist is not None]
        assert len(new_artists_album_ids) == len(resolved_album_artists)
        print(f"Successfully retrieved {len(resolved_album_artists)} artists...")

        for artist in resolved_album_artists:
            session.add(
                Artist(
                    image_url=artist["images"][0]["url"] if len(artist["images"]) > 0 else None,
                    spotify_url=artist["external_urls"]["spotify"],
                    **artist
                )
            )
        print(f"Successfully added {len(resolved_album_artists)} artists to db...")
        session.commit()

    with Session(engine) as session:
        added = set()
        for album in new_albums:
            if album["id"] in added:
                continue

            artists = album.pop('artists', [])
            session.add(
                Album(
                    image_url=album["images"][0]["url"] if len(album["images"]) > 0 else None,
                    spotify_url=album["external_urls"]["spotify"],
                    artists=[session.get(Artist, artist["id"]) for artist in artists],
                    **album
                )
            )
            added.add(album["id"])
            # for artist in artists:
            #     session.add(
            #         AlbumArtistLink(
            #             artist_id=artist["id"],
            #             album_id=album["id"],
            #         )
            #     )
        print(f"Successfully added {len(added)} albums to db...")
        session.commit()

        new_track_artists_ids = {
            artist['id'] for t in resolved_new_tracks for artist in t["artists"]
            if artist["id"] not in existing_artist_ids and artist["id"] not in new_artists_album_ids
        }
        print(f"There are {len(new_track_artists_ids)} new artists in the tracks...")
        print(f"Resolving {len(new_track_artists_ids)} new artists...")
        track_artist_futures = []
        for i in range(0, len(new_track_artists_ids), 10):
            track_artist_futures.append(get_artists_from_spotify(list(new_track_artists_ids)[i:i + 10], access_token))

        resolved_track_artists = [
            artist for response in (await asyncio.gather(*track_artist_futures)) for artist in response if
            artist is not None
        ]
        assert len(new_track_artists_ids) == len(resolved_track_artists)
        print(f"Successfully retrieved {len(resolved_track_artists)} artists...")

    with Session(engine) as session:
        for artist in resolved_track_artists:
            session.add(
                Artist(
                    image_url=artist["images"][0]["url"] if len(artist["images"]) > 0 else None,
                    spotify_url=artist["external_urls"]["spotify"],
                    **artist
                )
            )
        print(f"Successfully added {len(resolved_track_artists)} artists to db...")
        session.commit()

    with Session(engine) as session:
        for track in resolved_new_tracks:
            artists = track.pop('artists', [])
            album = track.pop('album', None)

            audio_features = resolved_audio_features.get(track["id"])
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
            # for artist in artists:
            #     session.add(
            #         TrackArtistLink(
            #             artist_id=artist["id"],
            #             track_id=track["id"],
            #         )
            #     )

        print(f"Successfully added {len(resolved_new_tracks)} tracks to db...")
        session.commit()


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
