from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Resume Analyzer"
    redis_url: str | None = None
    enable_llm: bool = False
    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
