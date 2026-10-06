
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str | None = None
    groq_api_key: str | None = None
    
    # Garante compatibilidade total caso algum agente chame em maiúsculas
    @property
    def GROQ_API_KEY(self):
        return self.groq_api_key

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_insensitive=True
    )

settings = Settings()