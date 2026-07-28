import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Clock3, Database, History, Minus, Play, Plus, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, KeyboardEvent, PointerEvent as ReactPointerEvent } from "react";
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

const SPLITTER_SIZE = 8;
const MIN_STATEMENT_WIDTH = 260;
const MIN_CODING_WIDTH = 330;
const MIN_EDITOR_HEIGHT = 260;
const MIN_RESULT_HEIGHT = 150;
const DEFAULT_STATEMENT_RATIO = 0.46;
const DEFAULT_EDITOR_RATIO = 0.66;
const MIN_CODE_FONT_SIZE = 12;
const MAX_CODE_FONT_SIZE = 20;
const DEFAULT_CODE_FONT_SIZE = 13;

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function readPreference(key: string, fallback: number, min: number, max: number) {
  try {
    const value = Number(window.localStorage.getItem(key));
    return Number.isFinite(value) && value >= min && value <= max ? value : fallback;
  } catch {
    return fallback;
  }
}

function storePreference(key: string, value: number) {
  try {
    window.localStorage.setItem(key, String(value));
  } catch {
    // The controls still work when browser storage is unavailable.
  }
}

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
    <div className="judge-result" key={`${submission.id}-${submission.status}`}>
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
  const [statementRatio, setStatementRatio] = useState(() => readPreference("oj-statement-ratio", DEFAULT_STATEMENT_RATIO, 0.2, 0.8));
  const [editorRatio, setEditorRatio] = useState(() => readPreference("oj-editor-ratio", DEFAULT_EDITOR_RATIO, 0.3, 0.85));
  const [codeFontSize, setCodeFontSize] = useState(() => readPreference("oj-code-font-size", DEFAULT_CODE_FONT_SIZE, MIN_CODE_FONT_SIZE, MAX_CODE_FONT_SIZE));
  const workspaceRef = useRef<HTMLDivElement>(null);
  const statementPaneRef = useRef<HTMLElement>(null);
  const codingPaneRef = useRef<HTMLElement>(null);
  const editorPanelRef = useRef<HTMLDivElement>(null);
  const resizeCleanupRef = useRef<(() => void) | null>(null);

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

  useEffect(() => () => resizeCleanupRef.current?.(), []);

  useEffect(() => storePreference("oj-statement-ratio", statementRatio), [statementRatio]);
  useEffect(() => storePreference("oj-editor-ratio", editorRatio), [editorRatio]);
  useEffect(() => storePreference("oj-code-font-size", codeFontSize), [codeFontSize]);

  const beginResize = (
    event: ReactPointerEvent<HTMLDivElement>,
    axis: "x" | "y",
    container: HTMLElement | null,
    leadingPanel: HTMLElement | null,
    minimumLeading: number,
    minimumTrailing: number,
    updateRatio: (ratio: number) => void,
  ) => {
    if (event.button !== 0 || !container || !leadingPanel || window.matchMedia("(max-width: 900px)").matches) return;

    const availableSize = (axis === "x" ? container.clientWidth : container.clientHeight) - SPLITTER_SIZE;
    const maximumLeading = availableSize - minimumTrailing;
    if (availableSize <= 0 || maximumLeading < minimumLeading) return;

    event.preventDefault();
    resizeCleanupRef.current?.();

    const startPointer = axis === "x" ? event.clientX : event.clientY;
    const startSize = axis === "x"
      ? leadingPanel.getBoundingClientRect().width
      : leadingPanel.getBoundingClientRect().height;
    const bodyClass = axis === "x" ? "is-resizing-column" : "is-resizing-row";

    const handlePointerMove = (moveEvent: PointerEvent) => {
      const pointer = axis === "x" ? moveEvent.clientX : moveEvent.clientY;
      const nextSize = clamp(startSize + pointer - startPointer, minimumLeading, maximumLeading);
      updateRatio(nextSize / availableSize);
    };

    const finishResize = () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", finishResize);
      window.removeEventListener("pointercancel", finishResize);
      window.removeEventListener("blur", finishResize);
      document.body.classList.remove(bodyClass);
      resizeCleanupRef.current = null;
    };

    resizeCleanupRef.current = finishResize;
    document.body.classList.add(bodyClass);
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", finishResize);
    window.addEventListener("pointercancel", finishResize);
    window.addEventListener("blur", finishResize);
  };

  const adjustSplit = (
    axis: "x" | "y",
    delta: number,
    container: HTMLElement | null,
    leadingPanel: HTMLElement | null,
    minimumLeading: number,
    minimumTrailing: number,
    updateRatio: (ratio: number) => void,
  ) => {
    if (!container || !leadingPanel) return;
    const availableSize = (axis === "x" ? container.clientWidth : container.clientHeight) - SPLITTER_SIZE;
    const currentSize = axis === "x"
      ? leadingPanel.getBoundingClientRect().width
      : leadingPanel.getBoundingClientRect().height;
    const maximumLeading = availableSize - minimumTrailing;
    if (availableSize <= 0 || maximumLeading < minimumLeading) return;
    updateRatio(clamp(currentSize + delta, minimumLeading, maximumLeading) / availableSize);
  };

  const handleColumnSeparatorKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const step = event.shiftKey ? 40 : 16;
    adjustSplit(
      "x",
      event.key === "ArrowLeft" ? -step : step,
      workspaceRef.current,
      statementPaneRef.current,
      MIN_STATEMENT_WIDTH,
      MIN_CODING_WIDTH,
      setStatementRatio,
    );
  };

  const handleRowSeparatorKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
    event.preventDefault();
    const step = event.shiftKey ? 40 : 16;
    adjustSplit(
      "y",
      event.key === "ArrowUp" ? -step : step,
      codingPaneRef.current,
      editorPanelRef.current,
      MIN_EDITOR_HEIGHT,
      MIN_RESULT_HEIGHT,
      setEditorRatio,
    );
  };

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
  const workspaceStyle = {
    "--statement-width": `calc(${statementRatio * 100}% - ${statementRatio * SPLITTER_SIZE}px)`,
  } as CSSProperties;
  const codingPaneStyle = {
    "--editor-height": `calc(${editorRatio * 100}% - ${editorRatio * SPLITTER_SIZE}px)`,
  } as CSSProperties;

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

      <div className="practice-workspace" ref={workspaceRef} style={workspaceStyle}>
        <article className="statement-pane" id="problem-statement-pane" ref={statementPaneRef}>
          <div className="pane-title"><strong>题目描述</strong><span>{problem.test_case_count} 个测试点</span></div>
          <div className="statement-scroll">
            <MarkdownRenderer>{statementMarkdown(problem)}</MarkdownRenderer>
          </div>
        </article>

        <div
          className="workspace-splitter column-splitter"
          role="separator"
          aria-label="调整题目描述和代码区域宽度"
          aria-controls="problem-statement-pane problem-coding-pane"
          aria-orientation="vertical"
          aria-valuemin={20}
          aria-valuemax={80}
          aria-valuenow={Math.round(statementRatio * 100)}
          tabIndex={0}
          title="拖拽调整宽度，双击恢复默认"
          onPointerDown={(event) => beginResize(event, "x", workspaceRef.current, statementPaneRef.current, MIN_STATEMENT_WIDTH, MIN_CODING_WIDTH, setStatementRatio)}
          onKeyDown={handleColumnSeparatorKeyDown}
          onDoubleClick={() => setStatementRatio(DEFAULT_STATEMENT_RATIO)}
        />

        <section className="coding-pane" id="problem-coding-pane" ref={codingPaneRef} style={codingPaneStyle}>
          <div className="editor-panel" id="problem-editor-panel" ref={editorPanelRef}>
            <div className="editor-toolbar">
              <div className="segmented-control" aria-label="编程语言">
                <button type="button" className={language === "cpp" ? "active" : ""} onClick={() => setLanguage("cpp")}>C++ 17</button>
                <button type="button" className={language === "c" ? "active" : ""} onClick={() => setLanguage("c")}>C 17</button>
              </div>
              <div className="editor-tools">
                <div className="font-size-control" aria-label="代码字体大小">
                  <button type="button" className="icon-button" onClick={() => setCodeFontSize((current) => clamp(current - 1, MIN_CODE_FONT_SIZE, MAX_CODE_FONT_SIZE))} disabled={codeFontSize === MIN_CODE_FONT_SIZE} aria-label="减小代码字体" title="减小代码字体"><Minus size={15} /></button>
                  <output aria-label={`当前代码字体 ${codeFontSize} 像素`}>{codeFontSize}px</output>
                  <button type="button" className="icon-button" onClick={() => setCodeFontSize((current) => clamp(current + 1, MIN_CODE_FONT_SIZE, MAX_CODE_FONT_SIZE))} disabled={codeFontSize === MAX_CODE_FONT_SIZE} aria-label="增大代码字体" title="增大代码字体"><Plus size={15} /></button>
                </div>
                <button type="button" className="icon-button" onClick={() => setCode(templates[language])} aria-label="重置代码" title="重置代码"><RotateCcw size={17} /></button>
              </div>
            </div>
            <CodeEditor value={code} onChange={setCode} minHeight="100%" fontSize={codeFontSize} />
            <div className="editor-actions">
              {submitMutation.error && <span className="inline-error" role="alert">{submitMutation.error.message}</span>}
              <span className="draft-state">草稿已自动保存</span>
              <button className="button primary submit-button" onClick={() => submitMutation.mutate()} disabled={submitMutation.isPending || !code.trim()}>
                <Play size={17} fill="currentColor" />{submitMutation.isPending ? "正在提交" : "提交代码"}
              </button>
            </div>
          </div>

          <div
            className="workspace-splitter row-splitter"
            role="separator"
            aria-label="调整代码编辑区和判题信息栏高度"
            aria-controls="problem-editor-panel problem-result-panel"
            aria-orientation="horizontal"
            aria-valuemin={30}
            aria-valuemax={85}
            aria-valuenow={Math.round(editorRatio * 100)}
            tabIndex={0}
            title="拖拽调整高度，双击恢复默认"
            onPointerDown={(event) => beginResize(event, "y", codingPaneRef.current, editorPanelRef.current, MIN_EDITOR_HEIGHT, MIN_RESULT_HEIGHT, setEditorRatio)}
            onKeyDown={handleRowSeparatorKeyDown}
            onDoubleClick={() => setEditorRatio(DEFAULT_EDITOR_RATIO)}
          />

          <div className="result-panel" id="problem-result-panel">
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
