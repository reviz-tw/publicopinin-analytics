from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus, urlparse

import httpx


@dataclass(frozen=True)
class SearchResult:
    posts: list[dict[str, Any]]
    comments: list[dict[str, Any]]


class ApifySearchClient:
    def __init__(self, token: str | None, actors: dict[str, str]):
        self.token = token
        self.actors = actors

    async def search(self, keyword: str, platform: str) -> SearchResult:
        if not self.token or platform not in self.actors:
            return self._dry_run_result(keyword, platform)

        actor_id = self.actors[platform]
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"https://api.apify.com/v2/acts/{quote_plus(actor_id)}/run-sync-get-dataset-items",
                params={"token": self.token},
                json={"search": keyword, "keyword": keyword, "query": keyword},
            )
            response.raise_for_status()
            items = response.json()

        posts = [self._normalize_item(item, keyword, platform, index) for index, item in enumerate(items)]
        comments = []
        for post, item in zip(posts, items, strict=False):
            for comment_index, comment in enumerate(item.get("comments") or []):
                comments.append(self._normalize_comment(comment, post["source_id"], platform, comment_index))
        return SearchResult(posts=posts, comments=comments)

    def _dry_run_result(self, keyword: str, platform: str) -> SearchResult:
        source_id = f"dry-run-{platform}-{keyword}".replace(" ", "-").lower()
        post = {
            "platform": platform,
            "source_id": source_id,
            "keyword": keyword,
            "author_name": "Dry Run Author",
            "author_handle": f"@{platform}_sample",
            "content": f"Sample {platform} post for keyword: {keyword}",
            "url": f"https://example.com/{platform}/{source_id}",
            "published_at": None,
            "like_count": 0,
            "comment_count": 1,
            "share_count": 0,
            "raw_json": {"dry_run": True, "keyword": keyword, "platform": platform},
        }
        comment = {
            "platform": platform,
            "post_source_id": source_id,
            "source_id": f"{source_id}-comment-1",
            "author_name": "Dry Run Commenter",
            "author_handle": f"@{platform}_commenter",
            "content": f"Sample comment for keyword: {keyword}",
            "published_at": None,
            "like_count": 0,
            "raw_json": {"dry_run": True, "keyword": keyword, "platform": platform, "parent_source_id": source_id},
        }
        return SearchResult(posts=[post], comments=[comment])

    def _normalize_item(self, item: dict[str, Any], keyword: str, platform: str, index: int) -> dict[str, Any]:
        source_id = str(item.get("id") or item.get("postId") or item.get("url") or f"{keyword}-{index}")
        author = item.get("author") if isinstance(item.get("author"), dict) else {}
        return {
            "platform": platform,
            "source_id": source_id,
            "keyword": keyword,
            "author_name": item.get("authorName") or author.get("name") or item.get("username"),
            "author_handle": item.get("authorHandle") or author.get("username") or item.get("handle"),
            "content": item.get("text") or item.get("caption") or item.get("content"),
            "url": item.get("url"),
            "published_at": item.get("timestamp") or item.get("publishedAt") or item.get("createdAt"),
            "like_count": item.get("likesCount") or item.get("likeCount"),
            "comment_count": item.get("commentsCount") or item.get("commentCount"),
            "share_count": item.get("sharesCount") or item.get("shareCount"),
            "raw_json": item,
        }

    def _normalize_comment(self, item: dict[str, Any], post_source_id: str, platform: str, index: int) -> dict[str, Any]:
        source_id = str(item.get("id") or item.get("commentId") or f"{post_source_id}-comment-{index}")
        author = item.get("author") if isinstance(item.get("author"), dict) else {}
        return {
            "platform": platform,
            "post_source_id": post_source_id,
            "source_id": source_id,
            "author_name": item.get("authorName") or author.get("name") or item.get("username"),
            "author_handle": item.get("authorHandle") or author.get("username") or item.get("handle"),
            "content": item.get("text") or item.get("content"),
            "published_at": item.get("timestamp") or item.get("publishedAt") or item.get("createdAt"),
            "like_count": item.get("likesCount") or item.get("likeCount"),
            "raw_json": item,
        }


class ApifyDatasetClient:
    def __init__(self, token: str | None):
        self.token = token

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    async def list_recent_datasets(self, limit: int) -> list[dict[str, Any]]:
        if not self.token:
            return []

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(
                "https://api.apify.com/v2/datasets",
                headers=self._headers(),
                params={"limit": limit, "desc": "true", "unnamed": "true"},
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("data", {}).get("items", [])

    async def get_dataset_items(self, dataset_id: str) -> list[dict[str, Any]]:
        if not self.token:
            return []

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(
                f"https://api.apify.com/v2/datasets/{quote_plus(dataset_id)}/items",
                headers=self._headers(),
                params={"clean": "true", "format": "json"},
            )
            response.raise_for_status()
            return response.json()


def infer_platform(item: dict[str, Any]) -> str:
    urls = _find_url_values(item)
    for url in urls:
        hostname = urlparse(url).hostname or ""
        hostname = hostname.lower()
        if "threads.net" in hostname or "threads.com" in hostname:
            return "threads"
        if "instagram.com" in hostname:
            return "instagram"
        if "facebook.com" in hostname or "fb.watch" in hostname:
            return "facebook"
        if "x.com" in hostname or "twitter.com" in hostname:
            return "x"
        if "tiktok.com" in hostname:
            return "tiktok"
    return "unknown"


def infer_keyword(item: dict[str, Any]) -> str:
    for key in ("keyword", "query", "searchTerm", "searchTerms", "searchQuery"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list) and value and isinstance(value[0], str) and value[0].strip():
            return value[0].strip()
    return "unknown"


def _find_url_values(value: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        urls.append(value)
    elif isinstance(value, dict):
        for nested in value.values():
            urls.extend(_find_url_values(nested))
    elif isinstance(value, list):
        for nested in value:
            urls.extend(_find_url_values(nested))
    return urls


def normalize_dataset_items(items: list[dict[str, Any]], keyword: str | None = None, platform: str | None = None) -> SearchResult:
    normalizer = ApifySearchClient(token=None, actors={})
    posts = [
        normalizer._normalize_item(
            item,
            keyword or infer_keyword(item),
            platform or infer_platform(item),
            index,
        )
        for index, item in enumerate(items)
    ]
    comments = []
    for post, item in zip(posts, items, strict=False):
        for comment_index, comment in enumerate(item.get("comments") or []):
            comments.append(normalizer._normalize_comment(comment, post["source_id"], platform, comment_index))
    return SearchResult(posts=posts, comments=comments)
