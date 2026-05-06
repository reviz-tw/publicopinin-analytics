import type { Analytics, AnalyticsFilters, PostFilters, PostList } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_AGGREGATOR_API_URL ?? "http://127.0.0.1:8000";

export function buildPostsUrl(filters: PostFilters): string {
  const url = new URL("/posts", API_BASE_URL);

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  return url.toString();
}

export async function fetchPosts(filters: PostFilters): Promise<PostList> {
  const response = await fetch(buildPostsUrl(filters), { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Aggregator request failed: ${response.status}`);
  }

  return response.json();
}

export async function fetchAnalytics(target = "國際特赦組織", filters: AnalyticsFilters = {}): Promise<Analytics> {
  const url = new URL("/analytics", API_BASE_URL);
  url.searchParams.set("target", target);
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  const response = await fetch(url.toString(), { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Aggregator analytics request failed: ${response.status}`);
  }

  return response.json();
}
