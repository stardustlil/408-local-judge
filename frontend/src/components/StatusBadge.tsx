import { CheckCircle2, CircleAlert, Clock3, LoaderCircle, XCircle } from "lucide-react";
import type { JudgeStatus } from "../types";

export const statusLabels: Record<JudgeStatus, string> = {
  Queued: "等待判题",
  Judging: "判题中",
  Accepted: "已通过",
  "Wrong Answer": "答案错误",
  "Compile Error": "编译错误",
  "Runtime Error": "运行错误",
  "Time Limit Exceeded": "超出时间限制",
  "Memory Limit Exceeded": "超出内存限制",
  "System Error": "系统错误",
};

export function statusTone(status: JudgeStatus) {
  if (status === "Accepted") return "accepted";
  if (status === "Queued" || status === "Judging") return "pending";
  if (status === "Wrong Answer") return "wrong";
  if (status === "Time Limit Exceeded" || status === "Memory Limit Exceeded") return "limited";
  return "error";
}

export function StatusBadge({ status, compact = false }: { status: JudgeStatus; compact?: boolean }) {
  const tone = statusTone(status);
  const Icon =
    status === "Accepted"
      ? CheckCircle2
      : status === "Queued"
        ? Clock3
        : status === "Judging"
          ? LoaderCircle
          : tone === "limited"
            ? CircleAlert
            : XCircle;
  return (
    <span className={`status-badge ${tone}${compact ? " compact" : ""}`}>
      <Icon size={compact ? 14 : 15} className={status === "Judging" ? "spin" : ""} />
      {statusLabels[status]}
    </span>
  );
}

