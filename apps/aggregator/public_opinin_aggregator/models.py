from pydantic import BaseModel, Field, field_validator


PLATFORMS = ("threads", "instagram", "facebook", "x", "tiktok")


class KeywordCreate(BaseModel):
    value: str = Field(min_length=1, max_length=200)

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Keyword cannot be blank")
        return normalized


class KeywordRead(BaseModel):
    id: int
    value: str
    is_active: bool
    created_at: str
    updated_at: str


class KeywordList(BaseModel):
    items: list[KeywordRead]


class SearchRunCreate(BaseModel):
    keywords: list[str] | None = None
    platforms: list[str] = Field(default_factory=lambda: list(PLATFORMS))

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = [keyword.strip() for keyword in value if keyword.strip()]
        if not normalized:
            raise ValueError("At least one keyword is required when keywords are provided")
        return normalized

    @field_validator("platforms")
    @classmethod
    def validate_platforms(cls, value: list[str]) -> list[str]:
        normalized = [platform.strip().lower() for platform in value if platform.strip()]
        invalid = sorted(set(normalized) - set(PLATFORMS))
        if invalid:
            raise ValueError(f"Unsupported platforms: {', '.join(invalid)}")
        if not normalized:
            raise ValueError("At least one platform is required")
        return normalized


class SearchRunRead(BaseModel):
    id: int
    status: str
    requested_keywords: list[str]
    requested_platforms: list[str]
    source: str = "debug"
    apify_run_id: str | None = None
    apify_actor_id: str | None = None
    apify_actor_task_id: str | None = None
    apify_dataset_id: str | None = None
    posts_count: int
    comments_count: int
    error_message: str | None
    started_at: str
    finished_at: str | None


class ApifyDatasetSyncCreate(BaseModel):
    platform: str
    keyword: str
    apify_run_id: str | None = None
    apify_actor_id: str | None = None
    apify_actor_task_id: str | None = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PLATFORMS:
            raise ValueError(f"Unsupported platform: {value}")
        return normalized

    @field_validator("keyword")
    @classmethod
    def normalize_keyword(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Keyword cannot be blank")
        return normalized


class ApifySyncRecentCreate(BaseModel):
    limit: int = Field(default=20, ge=1, le=1000)


class ApifySyncRecentRead(BaseModel):
    total: int
    synced: int
    skipped: int
    runs: list[SearchRunRead]


class PostRead(BaseModel):
    id: int
    platform: str
    source_id: str
    keyword: str
    author_name: str | None
    author_handle: str | None
    content: str | None
    url: str | None
    published_at: str | None
    like_count: int | None
    comment_count: int | None
    share_count: int | None
    collected_at: str


class PostList(BaseModel):
    total: int
    items: list[PostRead]
