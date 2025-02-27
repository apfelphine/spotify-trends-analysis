from typing import Any

import geojson
from geoalchemy2 import functions as func
from sqlalchemy import select
from sqlmodel import Session, or_

from app.database import engine
from app.models.countries import Country


async def get_map_with_features(country_feature_dict: dict[str, Any], feature_key: str) -> geojson.FeatureCollection:
    try:
        with (Session(engine) as session):
            where_filter = or_(*[Country.alpha_2_code == country for country in country_feature_dict.keys()])
            countries = session.exec(select(func.ST_AsGeoJSON(Country)).where(where_filter)).all()
            loaded_countries = []
            for c in countries:
                loaded_country = geojson.loads(c[0])
                alpha_2_code = loaded_country["properties"]["alpha_2_code"]
                loaded_country["properties"][feature_key] = country_feature_dict[alpha_2_code]
                loaded_countries.append(loaded_country)
            return geojson.FeatureCollection(features=loaded_countries)
    except Exception as e:
        print(str(e)[100:])
