from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"

    monday_api_token: str | None = None
    monday_api_url: str = "https://api.monday.com/v2"
    monday_api_version: str = "2025-04"
    monday_deals_board_id: int | None = None
    monday_work_orders_board_id: int | None = None

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
