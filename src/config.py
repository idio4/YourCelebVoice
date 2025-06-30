from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    qdrant_token: str = Field(..., alias="QDRANT_TOKEN")
    qdrant_url: str = Field(..., alias="QDRANT_URL")


settings = Settings()
