from pydantic import BaseModel
from pydantic_settings import BaseSettings


class _PostGresSettings(BaseModel):
    user: str
    password: str
    host: str
    port: int
    database_name: str


class Configuration(BaseSettings):
    postgres: _PostGresSettings

    class Config:
        env_nested_delimiter = '__'


configuration = Configuration()
