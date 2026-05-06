import Link from "next/link";
import { fetchPosts } from "../lib/api";
import type { Post, PostFilters } from "../lib/types";

export const dynamic = "force-dynamic";

type SearchParams = {
  keyword?: string;
  platform?: string;
  author?: string;
  q?: string;
  date_from?: string;
  date_to?: string;
  page?: string;
  page_size?: string;
};

type PageProps = {
  searchParams?: SearchParams;
};

const DEFAULT_PAGE_SIZE = 25;
const PLATFORM_OPTIONS = ["threads", "instagram", "facebook", "x", "tiktok", "unknown"];

function numberParam(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function pageHref(params: SearchParams, page: number): string {
  const next = new URLSearchParams();
  Object.entries({ ...params, page: String(page) }).forEach(([key, value]) => {
    if (value) {
      next.set(key, value);
    }
  });
  return `/?${next.toString()}`;
}

function compactDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  return value.replace("T", " ").replace("Z", "");
}

function engagement(post: Post): string {
  return `${post.like_count ?? 0} likes / ${post.comment_count ?? 0} comments / ${post.share_count ?? 0} shares`;
}

export default async function DashboardPage({ searchParams = {} }: PageProps) {
  const page = numberParam(searchParams.page, 1);
  const pageSize = numberParam(searchParams.page_size, DEFAULT_PAGE_SIZE);
  const offset = (page - 1) * pageSize;
  const filters: PostFilters = {
    keyword: searchParams.keyword,
    platform: searchParams.platform,
    author: searchParams.author,
    q: searchParams.q,
    date_from: searchParams.date_from,
    date_to: searchParams.date_to,
    limit: pageSize,
    offset,
  };

  let data = { total: 0, items: [] as Post[] };
  let error: string | null = null;

  try {
    data = await fetchPosts(filters);
  } catch (err) {
    error = err instanceof Error ? err.message : "Unable to load aggregator data";
  }

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));
  const clampedPage = Math.min(page, totalPages);
  const shownStart = data.total === 0 ? 0 : offset + 1;
  const shownEnd = Math.min(offset + data.items.length, data.total);

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <h1>Public Opinin Analytics</h1>
          <p>Review collected posts, narrow candidates, and inspect raw ingestion coverage.</p>
        </div>
        <div className="status">
          <span>{data.total}</span>
          <small>matching posts</small>
        </div>
      </header>

      <section className="summary" aria-label="Summary">
        <div>
          <span>{data.total}</span>
          <p>Total matches</p>
        </div>
        <div>
          <span>{shownStart}-{shownEnd}</span>
          <p>Visible range</p>
        </div>
        <div>
          <span>{clampedPage}/{totalPages}</span>
          <p>Page</p>
        </div>
        <div>
          <span>{pageSize}</span>
          <p>Rows per page</p>
        </div>
      </section>

      <form className="filters">
        <label>
          <span>Keyword</span>
          <input name="keyword" defaultValue={searchParams.keyword ?? ""} placeholder="unknown, policy..." />
        </label>
        <label>
          <span>Platform</span>
          <select name="platform" defaultValue={searchParams.platform ?? ""}>
            <option value="">All</option>
            {PLATFORM_OPTIONS.map((platform) => (
              <option key={platform} value={platform}>{platform}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Author</span>
          <input name="author" defaultValue={searchParams.author ?? ""} placeholder="Name or handle" />
        </label>
        <label>
          <span>Text</span>
          <input name="q" defaultValue={searchParams.q ?? ""} placeholder="Search content" />
        </label>
        <label>
          <span>From</span>
          <input name="date_from" type="datetime-local" defaultValue={searchParams.date_from ?? ""} />
        </label>
        <label>
          <span>To</span>
          <input name="date_to" type="datetime-local" defaultValue={searchParams.date_to ?? ""} />
        </label>
        <label>
          <span>Rows</span>
          <select name="page_size" defaultValue={String(pageSize)}>
            {[10, 25, 50, 100].map((size) => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
        </label>
        <input type="hidden" name="page" value="1" />
        <button type="submit">Apply</button>
        <Link className="reset" href="/">Reset</Link>
      </form>

      {error ? <p className="error">{error}</p> : null}

      <section className="tableShell">
        <div className="tableHeader">
          <p>{shownStart}-{shownEnd} of {data.total}</p>
          <nav className="pagination" aria-label="Pagination">
            <Link aria-disabled={clampedPage <= 1} className={clampedPage <= 1 ? "disabled" : ""} href={pageHref(searchParams, Math.max(1, clampedPage - 1))}>Previous</Link>
            <span>Page {clampedPage}</span>
            <Link aria-disabled={clampedPage >= totalPages} className={clampedPage >= totalPages ? "disabled" : ""} href={pageHref(searchParams, Math.min(totalPages, clampedPage + 1))}>Next</Link>
          </nav>
        </div>

        <div className="tableScroller">
          <table>
            <thead>
              <tr>
                <th>Platform</th>
                <th>Keyword</th>
                <th>Author</th>
                <th>Content</th>
                <th>Engagement</th>
                <th>Collected</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((post) => (
                <tr key={`${post.platform}-${post.source_id}-${post.id}`}>
                  <td><span className="platform">{post.platform}</span></td>
                  <td>{post.keyword}</td>
                  <td>
                    <strong>{post.author_handle ?? post.author_name ?? "-"}</strong>
                    {post.author_handle && post.author_name ? <small>{post.author_name}</small> : null}
                  </td>
                  <td className="contentCell">
                    {post.url ? <a href={post.url} target="_blank" rel="noreferrer">{post.content ?? post.url}</a> : post.content ?? "-"}
                  </td>
                  <td>{engagement(post)}</td>
                  <td>{compactDate(post.collected_at)}</td>
                </tr>
              ))}
              {data.items.length === 0 ? (
                <tr>
                  <td className="empty" colSpan={6}>No posts match the current filters.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
