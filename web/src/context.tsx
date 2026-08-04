import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { api } from "./api";
import { useWebSocket, type WsEvent } from "./ws";
import type { Health, Item, Library } from "./types";

export interface Toast {
  id: number;
  message: string;
  kind: "info" | "success" | "error";
}

interface AppContextValue {
  health: Health | null;
  libraries: Library[];
  items: Item[];
  loading: boolean;
  toasts: Toast[];
  notify: (message: string, kind?: Toast["kind"]) => void;
  refreshAll: () => Promise<void>;
  refreshItems: () => Promise<void>;
  refreshLibraries: () => Promise<void>;
  setItems: React.Dispatch<React.SetStateAction<Item[]>>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [libraries, setLibraries] = useState<Library[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastId = useRef(0);

  const notify = useCallback((message: string, kind: Toast["kind"] = "info") => {
    const id = ++toastId.current;
    setToasts((prev) => [...prev, { id, message, kind }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const refreshItems = useCallback(async () => {
    try {
      const data = await api.items();
      setItems(data);
    } catch (error) {
      console.warn("Failed to load items", error);
    }
  }, []);

  const refreshLibraries = useCallback(async () => {
    try {
      setLibraries(await api.libraries());
    } catch (error) {
      console.warn("Failed to load libraries", error);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    try {
      const [h, libs, it] = await Promise.allSettled([api.health(), api.libraries(), api.items()]);
      if (h.status === "fulfilled") setHealth(h.value);
      if (libs.status === "fulfilled") setLibraries(libs.value);
      if (it.status === "fulfilled") setItems(it.value);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleWs = useCallback(
    (event: WsEvent) => {
      if (event.name === "scan.completed" || event.name === "scan.started" || event.name === "metadata.completed") {
        refreshItems();
      }
      if (event.name === "metadata.completed" && event.data?.title) {
        notify(`Metadata updated: ${event.data.title}`, "success");
      }
      if (event.name === "metadata.failed") {
        notify(`Metadata failed: ${String(event.data?.error ?? "unknown error")}`, "error");
      }
      if (event.name === "optimize.completed") {
        notify("Optimization complete", "success");
        refreshItems();
      }
      if (event.name === "optimize.failed") {
        notify(`Optimization failed: ${String(event.data?.error ?? "unknown error")}`, "error");
      }
      if (event.name === "metadata.renamed" && event.data?.new) {
        notify(`Renamed to ${event.data.new}`, "info");
      }
    },
    [notify, refreshItems],
  );

  useWebSocket(handleWs);

  const value = useMemo(
    () => ({
      health,
      libraries,
      items,
      loading,
      toasts,
      notify,
      refreshAll,
      refreshItems,
      refreshLibraries,
      setItems,
    }),
    [health, libraries, items, loading, toasts, notify, refreshAll, refreshItems, refreshLibraries],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
