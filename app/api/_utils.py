import datetime
from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.business.data_import import get_min_max_date


class DateRange(BaseModel):
    from_date: Optional[datetime.datetime] = None
    to_date: Optional[datetime.datetime] = None

    @field_validator("from_date")
    @classmethod
    def validate_from_date(cls, from_date, info: ValidationInfo):
        if not from_date:
            return None

        to_date = info.data.get("to_date")
        if from_date and to_date and from_date > to_date:
            raise ValueError("to_date cannot be smaller than from_date")

        date_range = get_min_max_date()
        if from_date > date_range["to"].replace(tzinfo=datetime.timezone.utc):
            raise ValueError(f"from_date cannot be greater than {date_range['to']}")

        return from_date

    @field_validator("to_date")
    @classmethod
    def validate_to_date(cls, to_date, info: ValidationInfo):
        if not to_date:
            return None

        from_date = info.data.get("from_date")
        if from_date and to_date and from_date > to_date:
            raise ValueError("from_date cannot be greater than to_date")

        date_range = get_min_max_date()
        if to_date > date_range["to"].replace(tzinfo=datetime.timezone.utc):
            raise ValueError(f"to_date cannot be greater than {date_range['to']}")

        return to_date

