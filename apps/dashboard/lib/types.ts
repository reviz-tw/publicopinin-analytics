export type Post = {
  id: number;
  platform: string;
  source_id: string;
  keyword: string;
  author_name: string | null;
  author_handle: string | null;
  content: string | null;
  url: string | null;
  published_at: string | null;
  like_count: number | null;
  comment_count: number | null;
  share_count: number | null;
  collected_at: string;
};

export type PostList = {
  total: number;
  items: Post[];
};

export type PostFilters = {
  keyword?: string;
  platform?: string;
  author?: string;
  q?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
};
