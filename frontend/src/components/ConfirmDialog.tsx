import { AlertTriangle, X } from "lucide-react";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: string;
  confirmText?: string;
  busy?: boolean;
  onConfirm: () => void;
  onClose: () => void;
};

export function ConfirmDialog({
  open,
  title,
  description,
  confirmText = "确认删除",
  busy,
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  if (!open) return null;
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="dialog-title" onMouseDown={(event) => event.stopPropagation()}>
        <button className="icon-button dialog-close" onClick={onClose} aria-label="关闭" title="关闭">
          <X size={18} />
        </button>
        <span className="dialog-icon"><AlertTriangle size={22} /></span>
        <h2 id="dialog-title">{title}</h2>
        <p>{description}</p>
        <div className="dialog-actions">
          <button className="button secondary" onClick={onClose} disabled={busy}>取消</button>
          <button className="button danger" onClick={onConfirm} disabled={busy}>{busy ? "正在删除" : confirmText}</button>
        </div>
      </div>
    </div>
  );
}

