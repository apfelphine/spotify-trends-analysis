import os
from typing import Optional

from fastapi import APIRouter, UploadFile, HTTPException

from app.kaggle_import import load_songs_from_csv

router = APIRouter(
    tags=["status"],
)


@router.get("/health", status_code=200)
async def health():
    """Check if the service is healthy"""
    return "OK"


@router.post("/import")
async def import_data(file: UploadFile, version: Optional[str] = None):
    """Import spotify trend data from kaggle file"""
    if version is None:
        version = "unknown"

    try:
        contents = file.file.read()
        with open("/tmp/" + file.filename, 'wb') as f:
            f.write(contents)
    except Exception:
        raise HTTPException(status_code=500, detail='Couldn\'t read file')
    finally:
        file.file.close()

    new_trend_entries = await load_songs_from_csv("/tmp/" + file.filename, version)
    os.remove("/tmp/" + file.filename)

    return (f"Successfully added {new_trend_entries} "
            f"new entries to the database")
