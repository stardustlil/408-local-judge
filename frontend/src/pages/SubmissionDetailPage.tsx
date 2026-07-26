import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Clock3, Code2, ExternalLink, FileCode2 } from "lucide-react";
import { Link, useParams } from "react-router";
import { api } from "../api";
import { CodeEditor } from "../components/CodeEditor";
import { ErrorState, LoadingState } from "../components/PageState";
import { StatusBadge, statusLabels, statusTone } from "../components/StatusBadge";
import { formatDate, languageLabel } from "../utils";

export function SubmissionDetailPage() {
  const submissionId = Number(useParams().id);
  const submissionQuery = useQuery({
    queryKey: ["submission", submissionId],
    queryFn: () => api.getSubmission(submissionId),
    enabled: Number.isFinite(submissionId),
    refetchInterval: (query) => {
      const current = query.state.data;
      return !current || current.status === "Queued" || current.status === "Judging" ? 800 : false;
    },
  });

  if (submissionQuery.isLoading) return <LoadingState label="正在载入提交详情" />;
  if (submissionQuery.error || !submissionQuery.data) return <ErrorState error={submissionQuery.error} />;
  const submission = submissionQuery.data;

  return (
    <div className="page submission-detail-page">
      <header className="page-header detail-header">
        <div className="back-title">
          <Link className="icon-button" to="/submissions" aria-label="返回提交记录" title="返回"><ArrowLeft size={18} /></Link>
          <div><p className="eyebrow">提交 #{submission.id}</p><h1>{submission.problem_title}</h1></div>
        </div>
        <Link className="button secondary" to={`/problems/${submission.problem_id}`}>打开题目<ExternalLink size={16} /></Link>
      </header>

      <section className={`submission-verdict ${statusTone(submission.status)}`}>
        <StatusBadge status={submission.status} />
        <div className="verdict-copy"><strong>{submission.judge_message || statusLabels[submission.status]}</strong><span>{formatDate(submission.created_at)}</span></div>
        <div className="verdict-meta">
          <span><Code2 size={15} />{languageLabel(submission.language)}</span>
          <span><Clock3 size={15} />{submission.runtime_ms === null ? "-" : `最长 ${submission.runtime_ms} ms`}</span>
        </div>
      </section>

      {submission.case_results.length > 0 && (
        <section className="detail-section">
          <div className="section-heading"><h2>测试点</h2><span>{submission.case_results.filter((item) => item.status === "Accepted").length} / {submission.case_results.length} 通过</span></div>
          <div className="detail-case-list">
            {submission.case_results.map((item) => (
              <div className={`detail-case ${statusTone(item.status)}`} key={`${item.case}-${item.name}`}>
                <span className="case-order">#{item.case}</span>
                <div><strong>{item.name}</strong><small>{item.message}</small></div>
                <span>{item.status === "Accepted" ? `${item.time_ms} ms` : statusLabels[item.status]}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {submission.compile_output && (
        <section className="detail-section">
          <div className="section-heading"><h2>编译器输出</h2></div>
          <pre className="compiler-output">{submission.compile_output}</pre>
        </section>
      )}

      <section className="detail-section source-section">
        <div className="section-heading"><div><FileCode2 size={18} /><h2>提交代码</h2></div><span>{languageLabel(submission.language)}</span></div>
        <CodeEditor value={submission.source_code} readOnly minHeight="460px" />
      </section>
    </div>
  );
}
