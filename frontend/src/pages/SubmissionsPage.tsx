import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Filter, History } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { api } from "../api";
import { ErrorState, LoadingState } from "../components/PageState";
import { StatusBadge } from "../components/StatusBadge";
import type { JudgeStatus } from "../types";
import { formatDate, languageLabel } from "../utils";

const filters: { label: string; value: "" | JudgeStatus }[] = [
  { label: "全部结果", value: "" },
  { label: "已通过", value: "Accepted" },
  { label: "答案错误", value: "Wrong Answer" },
  { label: "编译错误", value: "Compile Error" },
  { label: "运行错误", value: "Runtime Error" },
  { label: "超出限制", value: "Time Limit Exceeded" },
];

export function SubmissionsPage() {
  const [statusFilter, setStatusFilter] = useState<"" | JudgeStatus>("");
  const submissionsQuery = useQuery({
    queryKey: ["submissions"],
    queryFn: () => api.getSubmissions(),
    refetchInterval: 2500,
  });
  const submissions = useMemo(() => (submissionsQuery.data ?? []).filter((item) => {
    if (!statusFilter) return true;
    if (statusFilter === "Time Limit Exceeded") return item.status === "Time Limit Exceeded" || item.status === "Memory Limit Exceeded";
    return item.status === statusFilter;
  }), [statusFilter, submissionsQuery.data]);

  if (submissionsQuery.isLoading) return <LoadingState label="正在载入提交记录" />;
  if (submissionsQuery.error) return <ErrorState error={submissionsQuery.error} />;
  const acceptedCount = (submissionsQuery.data ?? []).filter((item) => item.status === "Accepted").length;

  return (
    <div className="page">
      <header className="page-header">
        <div><p className="eyebrow">判题历史</p><h1>提交记录</h1><p className="page-subtitle">查看每次编译、运行和测试点结果。</p></div>
      </header>
      <section className="management-summary submissions-summary">
        <div><History size={19} /><span>共 <strong>{submissionsQuery.data?.length ?? 0}</strong> 次提交</span></div>
        <div><CheckCircle2 size={18} /><span>通过 <strong>{acceptedCount}</strong> 次</span></div>
      </section>
      <div className="list-toolbar submission-toolbar">
        <label className="select-field"><Filter size={16} /><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "" | JudgeStatus)} aria-label="筛选判题结果">{filters.map((item) => <option key={item.label} value={item.value}>{item.label}</option>)}</select></label>
        <span className="result-count">{submissions.length} 条记录</span>
      </div>
      <div className="problem-table-wrap">
        <table className="data-table submission-table">
          <thead><tr><th>提交</th><th>题目</th><th>结果</th><th>语言</th><th>最长用时</th><th>提交时间</th><th aria-label="操作" /></tr></thead>
          <tbody>
            {submissions.map((submission) => (
              <tr key={submission.id}>
                <td><span className="submission-id">#{submission.id}</span></td>
                <td><Link className="strong-link" to={`/problems/${submission.problem_id}`}>{submission.problem_title}</Link></td>
                <td><StatusBadge status={submission.status} compact /></td>
                <td><span className="language-pill">{languageLabel(submission.language)}</span></td>
                <td>{submission.runtime_ms === null ? "-" : `${submission.runtime_ms} ms`}</td>
                <td><time>{formatDate(submission.created_at)}</time></td>
                <td><Link className="icon-button row-action" to={`/submissions/${submission.id}`} aria-label="查看提交详情" title="查看详情"><ArrowRight size={17} /></Link></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!submissions.length && <div className="empty-list">暂无符合条件的提交记录</div>}
      </div>
    </div>
  );
}
