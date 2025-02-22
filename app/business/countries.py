import datetime
from typing import Optional

from sqlmodel import Session, select

from app.database import engine
from app.models.trends import TrendEntry


def get_all_countries(
    from_date: Optional[datetime.datetime] = None,
    to_date: Optional[datetime.datetime] = None,
) -> list[str]:
    with Session(engine) as session:
        statement = select(TrendEntry.country_code).distinct()
        if from_date is not None:
            statement = statement.where(TrendEntry.date >= from_date)
        if to_date is not None:
            statement = statement.where(TrendEntry.date <= to_date)

        return list(session.exec(statement).all())
