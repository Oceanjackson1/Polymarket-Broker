"use client";

import { useEffect, useRef, useState, useCallback } from "react";

type WSStatus = "connecting" | "connected" | "disconnected" | "error";

type UseWebSocketOptions<T> = {
  onMessage?: (data: T) => void;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  enabled?: boolean;
};

export function useWebSocket<T = unknown>(
  url: string,
  options: UseWebSocketOptions<T> = {}
) {
  const {
    onMessage,
    reconnectInterval = 3000,
    maxReconnectInterval = 30000,
    enabled = true,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<WSStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (!enabled || !url) return;

    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      retryRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as T;
        setData(parsed);
        onMessage?.(parsed);
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      setStatus("error");
    };

    ws.onclose = () => {
      setStatus("disconnected");
      wsRef.current = null;

      if (enabled) {
        const delay = Math.min(
          reconnectInterval * Math.pow(2, retryRef.current),
          maxReconnectInterval
        );
        retryRef.current += 1;
        timerRef.current = setTimeout(connect, delay);
      }
    };
  }, [url, enabled, onMessage, reconnectInterval, maxReconnectInterval]);

  useEffect(() => {
    connect();

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional close
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const send = useCallback((msg: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { data, status, send };
}
