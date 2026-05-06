from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/public_opinin.db"
    apify_token: str | None = None
    apify_actor_threads: str | None = None
    apify_actor_instagram: str | None = None
    apify_actor_facebook: str | None = None
    apify_actor_x: str | None = None
    apify_actor_tiktok: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )

    @property
    def apify_actors(self) -> dict[str, str]:
        return {
            platform: actor
            for platform, actor in {
                "threads": self.apify_actor_threads,
                "instagram": self.apify_actor_instagram,
                "facebook": self.apify_actor_facebook,
                "x": self.apify_actor_x,
                "tiktok": self.apify_actor_tiktok,
            }.items()
            if actor
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
