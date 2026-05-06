from collections import Counter
from datetime import datetime
from typing import Any


TOPIC_RULES = [
    ("人權與國際組織", ("國際特赦", "Amnesty", "人權", "Human Rights")),
    ("死刑與司法", ("死刑", "處決", "司法", "判決")),
    ("中國與台灣政治", ("中國", "台灣", "國民黨", "民進黨", "立法院", "政治")),
    ("移民與國籍", ("國籍", "移民", "配偶", "無國籍")),
    ("網路暴力與性別", ("網路霸凌", "霸凌", "騷擾", "女性", "性別")),
    ("動物與安樂死", ("安樂死", "流浪狗", "動物", "撲殺")),
]

TERM_GLOSSARY = (
    "國際特赦組織",
    "國際特赦",
    "Amnesty",
    "人權",
    "死刑",
    "中國",
    "台灣",
    "政治",
    "國籍",
    "移民",
    "女性",
    "網路霸凌",
    "安樂死",
    "動物",
    "立法院",
)

MAYBE_RELEVANT_TERMS = ("人權", "Amnesty", "死刑", "中國", "台灣", "政治", "司法", "移民", "國籍")


def build_analytics(posts: list[dict[str, Any]], target: str = "國際特赦組織") -> dict[str, Any]:
    return {
        "total_posts": len(posts),
        "volume_over_time": volume_over_time(posts),
        "topic_breakdown": topic_breakdown(posts),
        "top_terms": top_terms(posts),
        "relevance_distribution": relevance_distribution(posts, target),
        "top_posts": top_posts(posts, target),
    }


def volume_over_time(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for post in posts:
        counts[date_key(post.get("published_at") or post.get("collected_at"))] += 1
    return [{"date": date, "count": count} for date, count in sorted(counts.items())]


def topic_breakdown(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter(classify_topic(post.get("content") or "") for post in posts)
    return [
        {"label": topic, "count": count}
        for topic, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def top_terms(posts: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for post in posts:
        content = post.get("content") or ""
        for term in TERM_GLOSSARY:
            count = content.count(term)
            if count:
                counts[term] += count
    return [
        {"label": term, "count": count}
        for term, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def relevance_distribution(posts: list[dict[str, Any]], target: str) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter(classify_relevance(post.get("content") or "", target) for post in posts)
    order = ("highly_relevant", "maybe_relevant", "irrelevant")
    return [{"label": status, "count": counts.get(status, 0)} for status in order if counts.get(status, 0)]


def top_posts(posts: list[dict[str, Any]], target: str, limit: int = 10) -> list[dict[str, Any]]:
    scored = [(post, relevance_score(post.get("content") or "", target)) for post in posts]
    candidates = [item for item in scored if item[1] > 0] or scored
    ranked = sorted(
        candidates,
        key=lambda item: (-item[1], -engagement_score(item[0]), -int(item[0].get("id") or 0)),
    )
    return [{**post, "engagement_score": engagement_score(post)} for post, _score in ranked[:limit]]


def relevance_score(content: str, target: str) -> int:
    relevance = classify_relevance(content, target)
    if relevance == "highly_relevant":
        return 2
    if relevance == "maybe_relevant":
        return 1
    return 0


def classify_topic(content: str) -> str:
    for topic, terms in TOPIC_RULES:
        if any(term in content for term in terms):
            return topic
    return "其他與雜訊"


def classify_relevance(content: str, target: str) -> str:
    if target and target in content:
        return "highly_relevant"
    if "國際特赦" in content or "Amnesty" in content:
        return "highly_relevant"
    if any(term in content for term in MAYBE_RELEVANT_TERMS):
        return "maybe_relevant"
    return "irrelevant"


def engagement_score(post: dict[str, Any]) -> int:
    return int(post.get("like_count") or 0) + int(post.get("comment_count") or 0) + int(post.get("share_count") or 0)


def date_key(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        return value[:10]
