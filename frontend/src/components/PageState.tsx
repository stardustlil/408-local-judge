import { AlertTriangle, LoaderCircle } from "lucide-react";

export function LoadingState({ label = "正在加载" }: { label?: string }) {
  return (
    <div className="page-state">
      <LoaderCircle className="spin" size={22} />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ error }: { error: unknown }) {
  return (
    <div className="page-state error-state" role="alert">
      <AlertTriangle size={22} />
      <span>{error instanceof Error ? error.message : "加载失败，请刷新重试"}</span>
    </div>
  );
}

