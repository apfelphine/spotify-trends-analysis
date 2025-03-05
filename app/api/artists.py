from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import session_producer
from app.models.artists import Artist

router = APIRouter(
    tags=["artists"],
    prefix="/artists"
)

@router.get("", response_model=List[Artist])
async def get_all_artists(*, session: Session = Depends(session_producer)):
    """Retrieve all artists"""
    return list(session.exec(select(Artist)).unique().all())
