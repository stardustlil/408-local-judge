import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, ChevronDown, Eye, FileText, FileUp, FlaskConical, Plus, Save, Trash2, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api } from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { MarkdownRenderer } from "../components/MarkdownRenderer";
import { ErrorState, LoadingState } from "../components/PageState";
import { statementMarkdown } from "../statement";
import type { ProblemInput, TestCase } from "../types";
import { truncate } from "../utils";

const suggestedTags = ["顺序表", "链表", "栈", "队列", "树", "图", "排序", "查找", "哈希表", "递归"];

const emptyProblem: ProblemInput = {
  title: "",
  description: "",
  input_format: "",
  output_format: "",
  constraints: "",
  samples: [],
  tags: [],
  time_limit_ms: 1000,
  memory_limit_mb: 128,
};

function Field({ label, hint, children, wide = false }: { label: string; hint?: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <label className={`form-field${wide ? " wide" : ""}`}>
      <span>{label}{hint && <small>{hint}</small>}</span>
      {children}
    </label>
  );
}

function TestCaseManager({ problemId }: { problemId: number }) {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<"create" | "upload">("create");
  const [name, setName] = useState("");
  const [inputData, setInputData] = useState("");
  const [outputData, setOutputData] = useState("");
  const [inputFile, setInputFile] = useState<File | null>(null);
  const [outputFile, setOutputFile] = useState<File | null>(null);
  const [deleting, setDeleting] = useState<TestCase | null>(null);

  const casesQuery = useQuery({ queryKey: ["test-cases", problemId], queryFn: () => api.getTestCases(problemId) });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["test-cases", problemId] });
    queryClient.invalidateQueries({ queryKey: ["problem", problemId] });
    queryClient.invalidateQueries({ queryKey: ["problems"] });
  };
  const createMutation = useMutation({
    mutationFn: () => api.createTestCase(problemId, { name: name.trim() || `测试点 ${(casesQuery.data?.length ?? 0) + 1}`, input_data: inputData, output_data: outputData }),
    onSuccess: () => { setName(""); setInputData(""); setOutputData(""); refresh(); },
  });
  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!inputFile || !outputFile) throw new Error("请选择 input 和 output 文件");
      const data = new FormData();
      data.append("name", name.trim() || inputFile.name.replace(/\.[^.]+$/, ""));
      data.append("input_file", inputFile);
      data.append("output_file", outputFile);
      return api.uploadTestCase(problemId, data);
    },
    onSuccess: () => { setName(""); setInputFile(null); setOutputFile(null); refresh(); },
  });
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteTestCase(problemId, id),
    onSuccess: () => { setDeleting(null); refresh(); },
  });
  const actionError = createMutation.error ?? uploadMutation.error ?? deleteMutation.error;

  return (
    <section className="form-section test-manager">
      <div className="form-section-heading">
        <div><span className="section-index">04</span><div><h2>测试数据</h2><p>每次提交会依次运行这里的全部测试点。</p></div></div>
        <span className="count-badge">{casesQuery.data?.length ?? 0} 个</span>
      </div>

      <div className="test-layout">
        <div className="test-create-panel">
          <div className="segmented-control test-mode">
            <button type="button" className={mode === "create" ? "active" : ""} onClick={() => setMode("create")}><FlaskConical size={15} />直接创建</button>
            <button type="button" className={mode === "upload" ? "active" : ""} onClick={() => setMode("upload")}><FileUp size={15} />上传文件</button>
          </div>
          <Field label="测试点名称"><input value={name} onChange={(event) => setName(event.target.value)} placeholder={`测试点 ${(casesQuery.data?.length ?? 0) + 1}`} /></Field>
          {mode === "create" ? (
            <div className="test-data-fields">
              <Field label="Input"><textarea className="monospace-input" value={inputData} onChange={(event) => setInputData(event.target.value)} rows={7} placeholder="粘贴输入数据" /></Field>
              <Field label="Output"><textarea className="monospace-input" value={outputData} onChange={(event) => setOutputData(event.target.value)} rows={7} placeholder="粘贴标准输出" /></Field>
            </div>
          ) : (
            <div className="upload-fields">
              <label className={inputFile ? "file-drop selected" : "file-drop"}>
                {inputFile ? <Check size={20} /> : <Upload size={20} />}<span><strong>{inputFile?.name ?? "选择 input 文件"}</strong><small>UTF-8 文本，最大 2 MB</small></span>
                <input type="file" accept=".in,.txt,text/plain" onChange={(event) => setInputFile(event.target.files?.[0] ?? null)} />
              </label>
              <label className={outputFile ? "file-drop selected" : "file-drop"}>
                {outputFile ? <Check size={20} /> : <Upload size={20} />}<span><strong>{outputFile?.name ?? "选择 output 文件"}</strong><small>UTF-8 文本，最大 2 MB</small></span>
                <input type="file" accept=".out,.ans,.txt,text/plain" onChange={(event) => setOutputFile(event.target.files?.[0] ?? null)} />
              </label>
            </div>
          )}
          <button
            type="button"
            className="button secondary add-test-button"
            disabled={createMutation.isPending || uploadMutation.isPending || (mode === "upload" && (!inputFile || !outputFile))}
            onClick={() => mode === "create" ? createMutation.mutate() : uploadMutation.mutate()}
          >
            <Plus size={16} />{createMutation.isPending || uploadMutation.isPending ? "正在添加" : "添加测试点"}
          </button>
          {actionError && <p className="form-error" role="alert">{actionError.message}</p>}
        </div>

        <div className="test-case-list">
          {casesQuery.isLoading && <LoadingState label="正在载入测试点" />}
          {(casesQuery.data ?? []).map((testCase) => (
            <details className="test-case-item" key={testCase.id}>
              <summary>
                <span className="case-order">#{testCase.ordinal}</span>
                <strong>{testCase.name}</strong>
                <span>{testCase.input_data.length} / {testCase.output_data.length} 字符</span>
                <button type="button" className="icon-button danger-icon" onClick={(event) => { event.preventDefault(); setDeleting(testCase); }} aria-label="删除测试点" title="删除"><Trash2 size={15} /></button>
                <ChevronDown className="details-chevron" size={16} />
              </summary>
              <div className="test-preview-grid">
                <div><span>Input</span><pre>{truncate(testCase.input_data, 1000) || "<空>"}</pre></div>
                <div><span>Output</span><pre>{truncate(testCase.output_data, 1000) || "<空>"}</pre></div>
              </div>
            </details>
          ))}
          {!casesQuery.isLoading && !casesQuery.data?.length && <div className="empty-tests"><FlaskConical size={22} /><strong>还没有测试点</strong><span>至少添加一个测试点后才能提交代码。</span></div>}
        </div>
      </div>
      <ConfirmDialog
        open={deleting !== null}
        title="删除测试点"
        description={`确认删除“${deleting?.name ?? ""}”？此操作不会影响其他测试点。`}
        busy={deleteMutation.isPending}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
      />
    </section>
  );
}

export function ProblemEditorPage() {
  const params = useParams();
  const problemId = params.id ? Number(params.id) : null;
  const isNew = problemId === null;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ProblemInput>(emptyProblem);
  const [customTag, setCustomTag] = useState("");
  const [saved, setSaved] = useState(false);

  const problemQuery = useQuery({
    queryKey: ["problem", problemId],
    queryFn: () => api.getProblem(problemId!),
    enabled: problemId !== null,
  });

  useEffect(() => {
    if (!problemQuery.data) return;
    const { title, tags, time_limit_ms, memory_limit_mb } = problemQuery.data;
    setForm({
      title,
      description: statementMarkdown(problemQuery.data),
      input_format: "",
      output_format: "",
      constraints: "",
      samples: [],
      tags,
      time_limit_ms,
      memory_limit_mb,
    });
  }, [problemQuery.data]);

  const saveMutation = useMutation({
    mutationFn: () => isNew ? api.createProblem(form) : api.updateProblem(problemId, form),
    onSuccess: (problem) => {
      setSaved(true);
      queryClient.invalidateQueries({ queryKey: ["problems"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.setQueryData(["problem", problem.id], problem);
      window.setTimeout(() => setSaved(false), 1600);
      if (isNew) navigate(`/manage/${problem.id}`, { replace: true });
    },
  });

  const toggleTag = (tag: string) => setForm((current) => ({ ...current, tags: current.tags.includes(tag) ? current.tags.filter((item) => item !== tag) : [...current.tags, tag] }));
  const addCustomTag = () => {
    const value = customTag.trim();
    if (!value || form.tags.includes(value)) return;
    setForm((current) => ({ ...current, tags: [...current.tags, value] }));
    setCustomTag("");
  };
  const submit = (event: FormEvent) => { event.preventDefault(); saveMutation.mutate(); };

  if (!isNew && problemQuery.isLoading) return <LoadingState label="正在载入题目" />;
  if (!isNew && problemQuery.error) return <ErrorState error={problemQuery.error} />;

  return (
    <div className="page editor-page">
      <header className="page-header editor-page-header">
        <div className="back-title">
          <Link className="icon-button" to="/manage" aria-label="返回题目管理" title="返回"><ArrowLeft size={18} /></Link>
          <div><p className="eyebrow">{isNew ? "新建内容" : `题目 ${String(problemId).padStart(3, "0")}`}</p><h1>{isNew ? "创建题目" : "编辑题目"}</h1></div>
        </div>
        <button className="button primary" type="submit" form="problem-form" disabled={saveMutation.isPending}>
          {saved ? <Check size={17} /> : <Save size={17} />}{saveMutation.isPending ? "正在保存" : saved ? "已保存" : "保存题目"}
        </button>
      </header>

      <form id="problem-form" className="problem-form" onSubmit={submit}>
        <section className="form-section">
          <div className="form-section-heading"><div><span className="section-index">01</span><div><h2>基本信息</h2><p>标题和用于组织题库的知识点。</p></div></div></div>
          <div className="form-grid">
            <Field label="题目标题" wide><input required maxLength={200} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="例如：合并两个有序链表" /></Field>
            <div className="form-field wide">
              <span>知识点标签</span>
              <div className="tag-options">
                {suggestedTags.map((tag) => <button type="button" key={tag} className={form.tags.includes(tag) ? "tag-option selected" : "tag-option"} onClick={() => toggleTag(tag)}>{form.tags.includes(tag) && <Check size={13} />}{tag}</button>)}
              </div>
              <div className="inline-add"><input value={customTag} onChange={(event) => setCustomTag(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); addCustomTag(); } }} placeholder="添加自定义标签" /><button className="icon-button" type="button" onClick={addCustomTag} aria-label="添加标签" title="添加"><Plus size={17} /></button></div>
              {form.tags.filter((tag) => !suggestedTags.includes(tag)).length > 0 && <div className="tag-row custom-tags">{form.tags.filter((tag) => !suggestedTags.includes(tag)).map((tag) => <button type="button" className="tag removable" key={tag} onClick={() => toggleTag(tag)}>{tag} ×</button>)}</div>}
            </div>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-heading"><div><span className="section-index">02</span><div><h2>Markdown 题面</h2><p>使用一份完整文档组织描述、输入输出、样例和说明。</p></div></div></div>
          <div className="markdown-editor-grid">
            <label className="markdown-editor-pane">
              <span className="markdown-pane-title"><FileText size={15} />Markdown</span>
              <textarea
                required
                spellCheck={false}
                className="markdown-input monospace-input"
                rows={28}
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                placeholder={"# 题目标题\n\n## 题目描述\n\n...\n\n## 输入格式\n\n...\n\n## 输出格式\n\n..."}
              />
            </label>
            <div className="markdown-preview-pane">
              <span className="markdown-pane-title"><Eye size={15} />预览</span>
              <div className="markdown-preview-scroll">
                {form.description.trim() ? <MarkdownRenderer>{form.description}</MarkdownRenderer> : <span className="preview-empty">暂无内容</span>}
              </div>
            </div>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-heading"><div><span className="section-index">03</span><div><h2>判题限制</h2><p>配置每个测试点的运行资源上限。</p></div></div></div>
          <div className="limit-fields">
            <Field label="时间限制" hint="ms"><input type="number" min={100} max={10000} step={100} value={form.time_limit_ms} onChange={(event) => setForm({ ...form, time_limit_ms: Number(event.target.value) })} /></Field>
            <Field label="内存限制" hint="MB"><input type="number" min={16} max={1024} step={16} value={form.memory_limit_mb} onChange={(event) => setForm({ ...form, memory_limit_mb: Number(event.target.value) })} /></Field>
          </div>
        </section>

        {saveMutation.error && <p className="form-error" role="alert">{saveMutation.error.message}</p>}
      </form>

      {problemId !== null ? <TestCaseManager problemId={problemId} /> : (
        <section className="form-section test-manager disabled-section">
          <div className="form-section-heading"><div><span className="section-index">04</span><div><h2>测试数据</h2><p>保存题目后即可创建或上传测试点。</p></div></div></div>
        </section>
      )}
    </div>
  );
}
