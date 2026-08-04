import { useEffect, useRef } from "react";

export interface WsEvent {
  name: string;
  data: Record<string, unknown>;
  ts: number;
}

export function useWebSocket(onEvent: (event: WsEvent) => void): void {
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;
    let closedByUser = false;

    const connect = () => {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${proto}://${window.location.host}/ws`);

      socket.onopen = () => {
        console.info("[ws] connected");
      };

      socket.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data) as WsEvent;
          handlerRef.current(event);
        } catch {
          /* ignore malformed */
        }
      };

      socket.onclose = () => {
        if (!closedByUser) {
          reconnectTimer = window.setTimeout(connect, 3000);
        }
      };

      socket.onerror = () => {
        socket?.close();
      };
    };

    connect();

    return () => {
      closedByUser = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);
}
