import { useEffect, useRef, useState, type ReactNode } from "react";

export interface ContextAction {
  label: string;
  icon?: ReactNode;
  onClick?: () => void;
  danger?: boolean;
}

interface ContextState {
  x: number;
  y: number;
  actions: ContextAction[];
}

export function useContextMenu() {
  const [state, setState] = useState<ContextState | null>(null);

  const open = (x: number, y: number, actions: ContextAction[]) => {
    setState({ x, y, actions });
  };

  const close = () => setState(null);

  const render = state ? (
    <ContextMenuShell
      x={state.x}
      y={state.y}
      actions={state.actions}
      onClose={close}
    />
  ) : null;

  return { open, close, render, state };
}

function ContextMenuShell({
  x,
  y,
  actions,
  onClose,
}: {
  x: number;
  y: number;
  actions: ContextAction[];
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("mousedown", handleClick);
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("mousedown", handleClick);
      window.removeEventListener("keydown", handleKey);
    };
  }, [onClose]);

  useEffect(() => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const margin = 8;
    let left = x;
    let top = y;
    if (left + rect.width > window.innerWidth - margin) left = window.innerWidth - rect.width - margin;
    if (top + rect.height > window.innerHeight - margin) top = window.innerHeight - rect.height - margin;
    ref.current.style.left = `${Math.max(margin, left)}px`;
    ref.current.style.top = `${Math.max(margin, top)}px`;
  }, [x, y]);

  return (
    <div ref={ref} className="context-menu" style={{ left: x, top: y }}>
      {actions.map((action, i) =>
        action.label === "---" ? (
          <div key={i} className="context-divider" />
        ) : (
          <button
            key={i}
            className={`context-item${action.danger ? " danger" : ""}`}
            onClick={() => {
              onClose();
              action.onClick?.();
            }}
          >
            {action.icon}
            {action.label}
          </button>
        ),
      )}
    </div>
  );
}

/**
 * Hook to enable right-click on a target. Disables the native browser menu
 * and shows our custom menu.
 */
export function useRightClick(onContext: (e: React.MouseEvent, target: HTMLElement) => void) {
  const onContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    onContext(e, e.currentTarget as HTMLElement);
  };
  return { onContextMenu };
}
