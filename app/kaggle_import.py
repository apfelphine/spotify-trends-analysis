import datetime
import logging
import math

import kagglehub
import pandas as pd

from sqlmodel import SQLModel, Field, Session

from app.database import engine
from app.models.tracks import Track
from app.models.trends import TrendEntry


class DataImport(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    max_imported_date: datetime.datetime
    last_imported_version: str = Field(default="")


def import_songs_from_kaggle():
    path = kagglehub.dataset_download("asaniczka/top-spotify-songs-in-73-countries-daily-updated")
    current_version = path.split("/")[-1]

    with Session(engine) as session:
        last_import = session.get(DataImport, 1)

        if last_import is not None and last_import.last_imported_version == current_version:
            print(f"Already imported version {current_version}. Skipping import...")
            return

    load_songs_from_csv(path + '/universal_top_spotify_songs.csv', current_version)


def load_songs_from_csv(path: str, version: str) -> int:
    df = pd.read_csv(
        path,
        parse_dates=['snapshot_date', 'album_release_date']
    )

    with Session(engine) as session:
        last_import = session.get(DataImport, 1)

        if last_import is not None:
            # Delta-load
            df = df.loc[(df['snapshot_date'] > last_import.max_imported_date)]

        # Drop global entries (country is part of the primary key and must be given!)
        df.dropna(subset=['country'], inplace=True)

        # There are some rows with invalid data due to changes in spotify api. Drop those
        df.dropna(inplace=True)

        total_entries = len(df)
        if total_entries == 0:
            print("No new trend entries found...")
            return 0

        new_trend_entry_count = 0

        steps = math.ceil(total_entries / 25)

        logging.debug(
            f"Importing {total_entries} trend entries... "
            f"{new_trend_entry_count}/{total_entries} "
            f"({new_trend_entry_count/total_entries*100:.2f}%)"
        )

        for row in df.to_dict('records'):
            track_id = row["spotify_id"]

            # Check whether track was already trending before
            if session.get(Track, track_id) is None:
                session.add(
                    Track(
                        id=track_id,
                        explicit=row["is_explicit"],
                        **row
                    )
                )

            if session.get(
                    TrendEntry,
                    (row["snapshot_date"], row["country"], row["daily_rank"])
            ) is None:  # Some entries are double for some reason
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
                new_trend_entry_count += 1

            if new_trend_entry_count % steps == 0:
                logging.debug(
                    f"Importing {total_entries} trend entries... "
                    f"{new_trend_entry_count}/{total_entries} "
                    f"({new_trend_entry_count / total_entries * 100:.2f}%)"
                )

        if last_import is None:
            session.add(
                DataImport(
                    max_imported_date=df["snapshot_date"].max(),
                    last_imported_version=version,
                )
            )
        else:
            last_import.last_imported_version = version
            last_import.max_imported_date = df["snapshot_date"].max()

        session.commit()

    logging.debug("Finished.")
    return new_trend_entry_count
