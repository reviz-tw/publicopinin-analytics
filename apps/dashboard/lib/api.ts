import type { PostFilters, PostList } from "./types";

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
