from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import engine, get_async_session
from app.models.albums import Album, AlbumPublicWithArtists

router = APIRouter(
    tags=["albums"],
    prefix="/albums"
)


@router.get("", response_model=List[AlbumPublicWithArtists])
async def get_all_albums(*, session: Session = Depends(get_async_session)):
    """Retrieve all albums"""
    return list(session.exec(select(Album)).unique().all())
