from sqlmodel import SQLModel, create_engine

import logging

from app.models.configuration import configuration
from app.models.tracks import Track # noqa

logger = logging.getLogger(__name__)


class PostGISController:
    def __init__(self):
        # Connection to postgis
        self._engine = create_engine(
            f"postgresql+psycopg2://{configuration.postgres.user}:{configuration.postgres.password}"
            f"@{configuration.postgres.host}:{configuration.postgres.port}/"
            f"{configuration.postgres.database_name}",
            echo=True
        )

        # Create database and tables (if not exist)
        SQLModel.metadata.create_all(self._engine)

