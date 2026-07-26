import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, FilePlus2, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { api } from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ErrorState, LoadingState } from "../components/PageState";
import type { Problem } from "../types";

export function ManageProblemsPage() {
  const queryClient = useQueryClient();
  const [deleting, setDeleting] = useState<Problem | null>(null);
  const problemsQuery = useQuery({ queryKey: ["problems"], queryFn: api.getProblems });
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteProblem(id),
    onSuccess: () => {
      setDeleting(null);
      queryClient.invalidateQueries({ queryKey: ["problems"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  if (problemsQuery.isLoading) return <LoadingState label="正在载入题目管理" />;
  if (problemsQuery.error) return <ErrorState error={problemsQuery.error} />;

  return (
    <div className="page">
      <header className="page-header">
        <div><p className="eyebrow">内容工作台</p><h1>题目管理</h1><p className="page-subtitle">维护题面、样例与用于判题的测试数据。</p></div>
        <Link className="button primary" to="/manage/new"><Plus size={17} />新建题目</Link>
      </header>

      <section className="management-summary">
        <div><FilePlus2 size={19} /><span>当前共 <strong>{problemsQuery.data?.length ?? 0}</strong> 道题</span></div>
        <p>删除题目会同时删除其测试点和提交记录。</p>
      </section>

      <div className="problem-table-wrap manage-table-wrap">
        <table className="data-table manage-table">
          <thead><tr><th>ID</th><th>题目</th><th>知识点</th><th>测试点</th><th>提交</th><th>操作</th></tr></thead>
          <tbody>
            {(problemsQuery.data ?? []).map((problem) => (
              <tr key={problem.id}>
                <td><span className="problem-number">{String(problem.id).padStart(3, "0")}</span></td>
                <td><Link className="strong-link" to={`/manage/${problem.id}`}>{problem.title}</Link></td>
                <td><div className="tag-row">{problem.tags.map((tag) => <span className="tag" key={tag}>{tag}</span>)}</div></td>
                <td>{problem.test_case_count}</td>
                <td>{problem.submission_count}</td>
                <td>
                  <div className="row-buttons">
                    <Link className="icon-button" to={`/problems/${problem.id}`} aria-label="打开题目" title="打开题目"><ArrowRight size={17} /></Link>
                    <Link className="icon-button" to={`/manage/${problem.id}`} aria-label="编辑题目" title="编辑"><Pencil size={16} /></Link>
                    <button className="icon-button danger-icon" onClick={() => setDeleting(problem)} aria-label="删除题目" title="删除"><Trash2 size={16} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!problemsQuery.data?.length && <div className="empty-list">还没有题目</div>}
      </div>

      {deleteMutation.error && <p className="form-error" role="alert">{deleteMutation.error.message}</p>}
      <ConfirmDialog
        open={deleting !== null}
        title="删除题目"
        description={`“${deleting?.title ?? ""}”的题面、测试点和所有提交记录都会被永久删除。`}
        busy={deleteMutation.isPending}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
      />
    </div>
  );
}
