from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DEALS_", extra="ignore")

    database_url: str = "sqlite:///./deals.db"

    # Affiliate IDs appended to outbound links. Myntra/AJIO links arrive
    # already tracked from the affiliate network feed, so they need none here.
    amazon_associate_tag: str | None = None
    flipkart_affiliate_id: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
