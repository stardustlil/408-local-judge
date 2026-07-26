import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Circle, Filter, Plus, Search, Tags } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { api } from "../api";
import { ErrorState, LoadingState } from "../components/PageState";

export function ProblemListPage() {
  const [search, setSearch] = useState("");
  const [tag, setTag] = useState("");
  const problemsQuery = useQuery({ queryKey: ["problems"], queryFn: api.getProblems });
  const statsQuery = useQuery({ queryKey: ["stats"], queryFn: api.getStats });

  const tags = useMemo(() => {
    const counts = new Map<string, number>();
    for (const problem of problemsQuery.data ?? []) {
      for (const item of problem.tags) counts.set(item, (counts.get(item) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [problemsQuery.data]);

  const problems = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return (problemsQuery.data ?? []).filter((problem) => {
      const matchesSearch = !keyword || problem.title.toLowerCase().includes(keyword) || problem.tags.some((item) => item.toLowerCase().includes(keyword));
      return matchesSearch && (!tag || problem.tags.includes(tag));
    });
  }, [problemsQuery.data, search, tag]);

  if (problemsQuery.isLoading) return <LoadingState label="正在载入题库" />;
  if (problemsQuery.error) return <ErrorState error={problemsQuery.error} />;

  const stats = statsQuery.data;
  const acceptance = stats?.submission_count ? Math.round((stats.accepted_count / stats.submission_count) * 100) : 0;

  return (
    <div className="page page-list">
      <header className="page-header">
        <div>
          <p className="eyebrow">408 数据结构训练</p>
          <h1>题库</h1>
          <p className="page-subtitle">按知识点组织你的代码题训练进度。</p>
        </div>
        <Link className="button primary" to="/manage/new"><Plus size={17} />新建题目</Link>
      </header>

      <section className="stats-strip" aria-label="学习统计">
        <div><span>题目总数</span><strong>{stats?.problem_count ?? problems.length}</strong></div>
        <div><span>已通过</span><strong>{stats?.solved_count ?? 0}</strong></div>
        <div><span>累计提交</span><strong>{stats?.submission_count ?? 0}</strong></div>
        <div><span>提交通过率</span><strong>{acceptance}%</strong></div>
      </section>

      <div className="library-layout">
        <section className="problem-section">
          <div className="list-toolbar">
            <label className="search-field">
              <Search size={17} />
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索题目或知识点" aria-label="搜索题目" />
              {search && <button onClick={() => setSearch("")} aria-label="清空搜索">清除</button>}
            </label>
            <span className="result-count">{problems.length} 道题</span>
          </div>

          <div className="problem-table-wrap">
            <table className="data-table problem-table">
              <thead><tr><th>状态</th><th>题目</th><th>知识点</th><th>限制</th><th>测试点</th><th aria-label="操作" /></tr></thead>
              <tbody>
                {problems.map((problem) => (
                  <tr key={problem.id}>
                    <td>
                      {problem.accepted
                        ? <CheckCircle2 className="solved-icon" size={19} aria-label="已通过" />
                        : <Circle className="unsolved-icon" size={18} aria-label="未通过" />}
                    </td>
                    <td>
                      <Link className="problem-title-link" to={`/problems/${problem.id}`}>
                        <span className="problem-number">{String(problem.id).padStart(3, "0")}</span>
                        <strong>{problem.title}</strong>
                      </Link>
                    </td>
                    <td><div className="tag-row">{problem.tags.slice(0, 3).map((item) => <span className="tag" key={item}>{item}</span>)}</div></td>
                    <td><span className="limit-copy">{problem.time_limit_ms} ms · {problem.memory_limit_mb} MB</span></td>
                    <td><span className="test-count">{problem.test_case_count}</span></td>
                    <td><Link className="icon-button row-action" to={`/problems/${problem.id}`} aria-label={`打开${problem.title}`} title="开始练习"><ArrowRight size={17} /></Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {problems.length === 0 && <div className="empty-list">没有符合条件的题目</div>}
          </div>
        </section>

        <aside className="knowledge-panel">
          <div className="section-heading"><Tags size={18} /><h2>知识点</h2></div>
          <button className={!tag ? "tag-filter active" : "tag-filter"} onClick={() => setTag("")}>
            <span><Filter size={15} />全部题目</span><b>{problemsQuery.data?.length ?? 0}</b>
          </button>
          {tags.map(([item, count]) => (
            <button key={item} className={tag === item ? "tag-filter active" : "tag-filter"} onClick={() => setTag(item)}>
              <span>{item}</span><b>{count}</b>
            </button>
          ))}
        </aside>
      </div>
    </div>
  );
}
