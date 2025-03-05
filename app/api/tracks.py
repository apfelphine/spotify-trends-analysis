from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import session_producer
from app.models.tracks import Track, TrackPublicWithAlbumAndArtists

router = APIRouter(
    tags=["tracks"],
    prefix="/tracks"
)


@router.get("", response_model=List[TrackPublicWithAlbumAndArtists])
async def get_all_tracks(*, session: Session = Depends(session_producer)):
    """Retrieve all tracks"""
    return list(session.exec(select(Track)).unique().all())
