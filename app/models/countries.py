from typing import Any

from geoalchemy2 import Geometry
from sqlmodel import SQLModel, Field, Column


class Country(SQLModel, table=True):
    __tablename__ = "countries"
    alpha_2_code: str = Field(primary_key=True)

    name: str
    polygon: Any = Field(sa_column=Column(Geometry(geometry_type='MULTIPOLYGON'), nullable=False))
