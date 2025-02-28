from fastapi import APIRouter
from sqlmodel import Session, select

from app.database import engine
from app.models.tracks import Track

router = APIRouter(
    tags=["tracks"],
    prefix="/tracks"
)


@router.get("")
async def get_all_tracks() -> list[Track]:
    """Retrieve all tracks"""
    with (Session(engine) as session):
        return list(session.exec(select(Track)).all())
