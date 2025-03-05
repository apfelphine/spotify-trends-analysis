from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import session_producer
from app.models.albums import Album, AlbumPublicWithArtists

router = APIRouter(
    tags=["albums"],
    prefix="/albums"
)


@router.get("", response_model=List[AlbumPublicWithArtists])
async def get_all_albums(*, session: Session = Depends(session_producer)):
    """Retrieve all albums"""
    return list(session.exec(select(Album)).unique().all())
