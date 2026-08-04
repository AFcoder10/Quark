import { useApp } from "../context";

export function Toasts() {
  const { toasts } = useApp();
  if (toasts.length === 0) return null;
  return (
    <div className="toasts">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast ${toast.kind}`}>
          <span className="toast-dot" />
          {toast.message}
        </div>
      ))}
    </div>
  );
}
