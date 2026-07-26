import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Clock3, Database, History, Play, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import { api } from "../api";
import { CodeEditor } from "../components/CodeEditor";
import { MarkdownRenderer } from "../components/MarkdownRenderer";
import { ErrorState, LoadingState } from "../components/PageState";
import { StatusBadge, statusLabels, statusTone } from "../components/StatusBadge";
import type { Submission } from "../types";
import { statementMarkdown } from "../statement";
import { formatDate, languageLabel } from "../utils";

const templates = {
  cpp: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // 在这里编写代码

    return 0;
}
`,
  c: `#include <stdio.h>

int main(void) {
    // 在这里编写代码

    return 0;
}
`,
};

function ResultPanel({ submission }: { submission: Submission | undefined }) {
  if (!submission) {
    return (
      <div className="result-placeholder">
        <Play size={20} />
        <div><strong>等待提交</strong><span>判题结果将在这里显示</span></div>
      </div>
    );
  }
  const pending = submission.status === "Queued" || submission.status === "Judging";
  return (
    <div className="judge-result">
      <div className="result-summary">
        <StatusBadge status={submission.status} />
        {!pending && submission.runtime_ms !== null && <span><Clock3 size={15} /> 最长 {submission.runtime_ms} ms</span>}
        <span>提交 #{submission.id}</span>
      </div>
      {pending ? (
        <div className="judging-progress"><i /><span>{submission.judge_message || "正在准备沙箱"}</span></div>
      ) : (
        <>
          <p className={`judge-message ${statusTone(submission.status)}`}>{submission.judge_message}</p>
          {submission.case_results.length > 0 && (
            <div className="case-grid">
              {submission.case_results.map((item) => (
                <div className={`case-item ${statusTone(item.status)}`} key={`${item.case}-${item.name}`} title={item.message}>
                  <span>#{item.case}</span>
                  <strong>{item.name}</strong>
                  <small>{item.status === "Accepted" ? `${item.time_ms} ms` : statusLabels[item.status]}</small>
                </div>
              ))}
            </div>
          )}
          {submission.compile_output && (
            <details className="diagnostic-block" open={submission.status === "Compile Error"}>
              <summary>编译器输出</summary>
              <pre>{submission.compile_output}</pre>
            </details>
          )}
        </>
      )}
    </div>
  );
}

export function ProblemPage() {
  const params = useParams();
  const problemId = Number(params.id);
  const queryClient = useQueryClient();
  const [language, setLanguage] = useState<"c" | "cpp">("cpp");
  const [code, setCode] = useState(templates.cpp);
  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [resultTab, setResultTab] = useState<"result" | "recent">("result");

  const problemQuery = useQuery({
    queryKey: ["problem", problemId],
    queryFn: () => api.getProblem(problemId),
    enabled: Number.isFinite(problemId),
  });
  const recentQuery = useQuery({
    queryKey: ["submissions", problemId],
    queryFn: () => api.getSubmissions(problemId),
    enabled: Number.isFinite(problemId),
    refetchInterval: 3000,
  });
  const resultQuery = useQuery({
    queryKey: ["submission", submissionId],
    queryFn: () => api.getSubmission(submissionId!),
    enabled: submissionId !== null,
    refetchInterval: (query) => {
      const current = query.state.data;
      return !current || current.status === "Queued" || current.status === "Judging" ? 700 : false;
    },
  });

  useEffect(() => {
    const stored = localStorage.getItem(`oj-draft-${problemId}-${language}`);
    setCode(stored ?? templates[language]);
  }, [problemId, language]);

  useEffect(() => {
    if (!Number.isFinite(problemId)) return;
    const timer = window.setTimeout(() => localStorage.setItem(`oj-draft-${problemId}-${language}`, code), 250);
    return () => window.clearTimeout(timer);
  }, [problemId, language, code]);

  useEffect(() => {
    const result = resultQuery.data;
    if (!result || result.status === "Queued" || result.status === "Judging") return;
    queryClient.invalidateQueries({ queryKey: ["submissions", problemId] });
    queryClient.invalidateQueries({ queryKey: ["problem", problemId] });
    queryClient.invalidateQueries({ queryKey: ["problems"] });
    queryClient.invalidateQueries({ queryKey: ["stats"] });
  }, [problemId, queryClient, resultQuery.data]);

  const submitMutation = useMutation({
    mutationFn: () => api.createSubmission(problemId, language, code),
    onSuccess: (submission) => {
      setSubmissionId(submission.id);
      setResultTab("result");
      queryClient.setQueryData(["submission", submission.id], submission);
      queryClient.invalidateQueries({ queryKey: ["submissions", problemId] });
    },
  });

  const latest = resultQuery.data ?? (submissionId === null ? recentQuery.data?.[0] : undefined);
  const titleParts = useMemo(() => problemQuery.data?.title ?? "题目", [problemQuery.data]);

  if (problemQuery.isLoading) return <LoadingState label="正在载入题目" />;
  if (problemQuery.error || !problemQuery.data) return <ErrorState error={problemQuery.error} />;
  const problem = problemQuery.data;

  return (
    <div className="problem-page">
      <header className="problem-topbar">
        <div className="problem-identity">
          <Link className="icon-button" to="/" aria-label="返回题库" title="返回题库"><ArrowLeft size={18} /></Link>
          <div><span>题目 {String(problem.id).padStart(3, "0")}</span><h1>{titleParts}</h1></div>
        </div>
        <div className="problem-meta">
          <span><Clock3 size={15} />{problem.time_limit_ms} ms</span>
          <span><Database size={15} />{problem.memory_limit_mb} MB</span>
          {problem.tags.map((tag) => <span className="tag" key={tag}>{tag}</span>)}
        </div>
      </header>

      <div className="practice-workspace">
        <article className="statement-pane">
          <div className="pane-title"><strong>题目描述</strong><span>{problem.test_case_count} 个测试点</span></div>
          <div className="statement-scroll">
            <MarkdownRenderer>{statementMarkdown(problem)}</MarkdownRenderer>
          </div>
        </article>

        <section className="coding-pane">
          <div className="editor-toolbar">
            <div className="segmented-control" aria-label="编程语言">
              <button className={language === "cpp" ? "active" : ""} onClick={() => setLanguage("cpp")}>C++ 17</button>
              <button className={language === "c" ? "active" : ""} onClick={() => setLanguage("c")}>C 17</button>
            </div>
            <button className="icon-button" onClick={() => setCode(templates[language])} aria-label="重置代码" title="重置代码"><RotateCcw size={17} /></button>
          </div>
          <CodeEditor value={code} onChange={setCode} />
          <div className="editor-actions">
            {submitMutation.error && <span className="inline-error" role="alert">{submitMutation.error.message}</span>}
            <span className="draft-state">草稿已自动保存</span>
            <button className="button primary submit-button" onClick={() => submitMutation.mutate()} disabled={submitMutation.isPending || !code.trim()}>
              <Play size={17} fill="currentColor" />{submitMutation.isPending ? "正在提交" : "提交代码"}
            </button>
          </div>

          <div className="result-panel">
            <div className="result-tabs">
              <button className={resultTab === "result" ? "active" : ""} onClick={() => setResultTab("result")}>判题结果</button>
              <button className={resultTab === "recent" ? "active" : ""} onClick={() => setResultTab("recent")}><History size={15} />最近提交</button>
            </div>
            {resultTab === "result" ? (
              <ResultPanel submission={latest} />
            ) : (
              <div className="recent-submissions">
                {(recentQuery.data ?? []).slice(0, 5).map((item) => (
                  <Link to={`/submissions/${item.id}`} key={item.id}>
                    <StatusBadge status={item.status} compact />
                    <span>{languageLabel(item.language)}</span>
                    <time>{formatDate(item.created_at)}</time>
                  </Link>
                ))}
                {!recentQuery.data?.length && <div className="empty-list compact">暂无提交记录</div>}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
