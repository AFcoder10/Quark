import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { Item } from "./types";
import { Player } from "./components/Player";

interface PlayerContextValue {
  play: (item: Item) => void;
  close: () => void;
}

const PlayerContext = createContext<PlayerContextValue | null>(null);

export function PlayerProvider({ children }: { children: ReactNode }) {
  const [item, setItem] = useState<Item | null>(null);

  const play = useCallback((next: Item) => setItem(next), []);
  const close = useCallback(() => setItem(null), []);

  const value = useMemo(() => ({ play, close }), [play, close]);

  return (
    <PlayerContext.Provider value={value}>
      {children}
      {item && <Player item={item} onClose={close} />}
    </PlayerContext.Provider>
  );
}

export function usePlayer(): PlayerContextValue {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error("usePlayer must be used within PlayerProvider");
  return ctx;
}
