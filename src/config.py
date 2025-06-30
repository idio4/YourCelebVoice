from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    qdrant_token: str = Field(..., alias="QDRANT_TOKEN")
    qdrant_url: str = Field(..., alias="QDRANT_URL")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
