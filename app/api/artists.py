from fastapi import APIRouter
from sqlmodel import Session, select

from app.database import engine
from app.models.artists import Artist

router = APIRouter(
    tags=["artists"],
    prefix="/artists"
)


@router.get("")
async def get_all_artists() -> list[Artist]:
    """Retrieve all artists"""
    with (Session(engine) as session):
        return list(session.exec(select(Artist)).all())
