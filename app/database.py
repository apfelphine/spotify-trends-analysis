from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.models.configuration import configuration

engine = create_engine(
    f"postgresql+psycopg2://{configuration.postgres.user}:{configuration.postgres.password}"
    f"@{configuration.postgres.host}:{configuration.postgres.port}/"
    f"{configuration.postgres.database_name}",
    echo=False,
    plugins=["geoalchemy2"]
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_async_session():
    with Session(engine) as session:
        yield session
