import Link from "next/link";
import { fetchAnalytics, fetchPosts } from "../lib/api";
import type { Analytics, CountPoint, Post, PostFilters, TimePoint } from "../lib/types";

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
  tab?: string;
};

type PageProps = {
  searchParams?: SearchParams;
};

const DEFAULT_PAGE_SIZE = 25;
const PLATFORM_OPTIONS = ["threads", "instagram", "facebook", "x", "tiktok", "unknown"];
const TARGET = "國際特赦組織";

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
  const activeTab = searchParams.tab === "visualization" ? "visualization" : "all";
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
  let analytics: Analytics | null = null;
  let error: string | null = null;

  try {
    if (activeTab === "visualization") {
      analytics = await fetchAnalytics(TARGET);
    } else {
      data = await fetchPosts(filters);
    }
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
          <span>{activeTab === "visualization" ? analytics?.total_posts ?? 0 : data.total}</span>
          <small>{activeTab === "visualization" ? "analyzed posts" : "matching posts"}</small>
        </div>
      </header>

      <nav className="tabs" aria-label="Dashboard tabs">
        <Link className={activeTab === "all" ? "active" : ""} href="/">所有資料</Link>
        <Link className={activeTab === "visualization" ? "active" : ""} href="/?tab=visualization">資料視覺化</Link>
      </nav>

      {activeTab === "visualization" ? (
        <VisualizationTab analytics={analytics} error={error} />
      ) : (
        <AllDataTab
          data={data}
          error={error}
          searchParams={searchParams}
          pageSize={pageSize}
          shownStart={shownStart}
          shownEnd={shownEnd}
          clampedPage={clampedPage}
          totalPages={totalPages}
        />
      )}
    </main>
  );
}

function AllDataTab({
  data,
  error,
  searchParams,
  pageSize,
  shownStart,
  shownEnd,
  clampedPage,
  totalPages,
}: {
  data: { total: number; items: Post[] };
  error: string | null;
  searchParams: SearchParams;
  pageSize: number;
  shownStart: number;
  shownEnd: number;
  clampedPage: number;
  totalPages: number;
}) {
  return (
    <>
      <section className="summary" aria-label="Summary">
        <Metric value={data.total} label="Total matches" />
        <Metric value={`${shownStart}-${shownEnd}`} label="Visible range" />
        <Metric value={`${clampedPage}/${totalPages}`} label="Page" />
        <Metric value={pageSize} label="Rows per page" />
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

      <PostsTable
        posts={data.items}
        header={`${shownStart}-${shownEnd} of ${data.total}`}
        searchParams={searchParams}
        clampedPage={clampedPage}
        totalPages={totalPages}
      />
    </>
  );
}

function VisualizationTab({ analytics, error }: { analytics: Analytics | null; error: string | null }) {
  if (error) {
    return <p className="error">{error}</p>;
  }

  if (!analytics) {
    return <p className="error">No analytics data available.</p>;
  }

  return (
    <>
      <section className="summary" aria-label="Visualization summary">
        <Metric value={analytics.total_posts} label="Analyzed posts" />
        <Metric value={analytics.topic_breakdown.length} label="Detected topics" />
        <Metric value={analytics.top_terms.length} label="Tracked terms" />
        <Metric value={analytics.top_posts.length} label="Ranked posts" />
      </section>

      <section className="vizGrid">
        <Panel title="Volume over time">
          <TimeBars points={analytics.volume_over_time} />
        </Panel>
        <Panel title="Topic breakdown">
          <HorizontalBars points={analytics.topic_breakdown} />
        </Panel>
        <Panel title="Top terms">
          <TermCloud points={analytics.top_terms} />
        </Panel>
        <Panel title="Relevance distribution">
          <HorizontalBars points={analytics.relevance_distribution} />
        </Panel>
      </section>

      <section className="tableShell">
        <div className="tableHeader">
          <p>Top posts and repeated narratives</p>
        </div>
        <PostsOnlyTable posts={analytics.top_posts} />
      </section>
    </>
  );
}

function Metric({ value, label }: { value: string | number; label: string }) {
  return (
    <div>
      <span>{value}</span>
      <p>{label}</p>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function HorizontalBars({ points }: { points: CountPoint[] }) {
  const max = Math.max(1, ...points.map((point) => point.count));
  return (
    <div className="bars">
      {points.map((point) => (
        <div className="barRow" key={point.label}>
          <div className="barMeta">
            <span>{point.label}</span>
            <strong>{point.count}</strong>
          </div>
          <div className="barTrack">
            <div className="barFill" style={{ width: `${(point.count / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function TimeBars({ points }: { points: TimePoint[] }) {
  const max = Math.max(1, ...points.map((point) => point.count));
  return (
    <div className="timeBars">
      {points.slice(-14).map((point) => (
        <div className="timeBar" key={point.date}>
          <div style={{ height: `${Math.max(8, (point.count / max) * 120)}px` }} />
          <span>{point.date}</span>
          <strong>{point.count}</strong>
        </div>
      ))}
    </div>
  );
}

function TermCloud({ points }: { points: CountPoint[] }) {
  return (
    <div className="terms">
      {points.map((point) => (
        <span key={point.label}>
          {point.label}<strong>{point.count}</strong>
        </span>
      ))}
    </div>
  );
}

function PostsTable({
  posts,
  header,
  searchParams,
  clampedPage,
  totalPages,
}: {
  posts: Post[];
  header: string;
  searchParams: SearchParams;
  clampedPage: number;
  totalPages: number;
}) {
  return (
    <section className="tableShell">
      <div className="tableHeader">
        <p>{header}</p>
        <nav className="pagination" aria-label="Pagination">
          <Link aria-disabled={clampedPage <= 1} className={clampedPage <= 1 ? "disabled" : ""} href={pageHref(searchParams, Math.max(1, clampedPage - 1))}>Previous</Link>
          <span>Page {clampedPage}</span>
          <Link aria-disabled={clampedPage >= totalPages} className={clampedPage >= totalPages ? "disabled" : ""} href={pageHref(searchParams, Math.min(totalPages, clampedPage + 1))}>Next</Link>
        </nav>
      </div>
      <PostsOnlyTable posts={posts} />
    </section>
  );
}

function PostsOnlyTable({ posts }: { posts: Post[] }) {
  return (
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
          {posts.map((post) => (
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
          {posts.length === 0 ? (
            <tr>
              <td className="empty" colSpan={6}>No posts match the current filters.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
