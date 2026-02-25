from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str

    # EEX source
    eex_base_url: str = "https://www.eex.com"

    # Sync scheduler
    sync_enabled: bool = True
    sync_schedule_hour: int = 6
    sync_schedule_minute: int = 0

    # Logging
    log_level: str = "INFO"

    # CORS (comma-separated list of allowed origins)
    cors_origins: str = "http://localhost:5173"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()
