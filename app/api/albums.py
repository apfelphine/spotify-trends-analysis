from fastapi import APIRouter
from sqlmodel import Session, select

from app.database import engine
from app.models.albums import Album

router = APIRouter(
    tags=["albums"],
    prefix="/albums"
)


@router.get("")
async def get_all_albums() -> list[Album]:
    """Retrieve all albums"""
    with (Session(engine) as session):
        return list(session.exec(select(Album)).all())
