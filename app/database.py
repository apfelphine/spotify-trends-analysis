from sqlalchemy import create_engine
from sqlmodel import SQLModel

from app.models.configuration import configuration

engine = create_engine(
    f"postgresql+psycopg2://{configuration.postgres.user}:{configuration.postgres.password}"
    f"@{configuration.postgres.host}:{configuration.postgres.port}/"
    f"{configuration.postgres.database_name}",
    echo=False
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
