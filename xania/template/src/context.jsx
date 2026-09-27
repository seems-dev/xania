import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";

const StateContext = createContext({
  state: {},
  sendEvent: () => {},
  connected: false,
});

export function StateProvider({ children }) {
  const [state, setState] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    const isOpen = wsRef.current && (wsRef.current.readyState === 1 || wsRef.current.readyState === (window.WebSocket?.OPEN ?? 1));
    if (isOpen) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    let wsPath = "/ws";
    const previewMatch = window.location.pathname.match(/^(\/preview\/[^/]+)/);
    if (previewMatch) {
      wsPath = previewMatch[1] + "/ws";
    }
    const wsUrl = `${protocol}//${host}${wsPath}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[Xania] Connected to state server via WebSocket");
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "init") {
          setState(msg.state || {});
        } else if (msg.type === "update") {
          if (msg.delta) {
            setState((prev) => ({ ...prev, ...msg.delta }));
          }
          if (msg.events && Array.isArray(msg.events)) {
            for (const ev of msg.events) {
              if (ev.type === "redirect") {
                window.location.href = ev.path;
              } else if (ev.type === "toast") {
                console.info(`[Xania Toast]: ${ev.message}`);
              } else if (ev.type === "console_log") {
                console.log(...(ev.data || []));
              }
            }
          }
        }
      } catch (err) {
        console.error("[Xania] Failed to parse WebSocket message:", err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log("[Xania] Reconnecting to server...");
        connect();
      }, 1000);
    };

    ws.onerror = (err) => {
      console.error("[Xania] WebSocket error:", err);
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const sendEvent = useCallback((name, payload = {}) => {
    // 1. Optimistic Local React State Updates for zero-latency UI
    const action = name.includes(".") ? name.split(".").pop() : name;
    setState((prev) => {
      const next = { ...prev };
      if (action === "like" || action === "increment") {
        const key = "likes" in next ? "likes" : ("count" in next ? "count" : Object.keys(next)[0] || "likes");
        const curr = typeof next[key] === "number" ? next[key] : parseInt(next[key] || 0, 10);
        next[key] = isNaN(curr) ? 1 : curr + 1;
      } else if (action === "decrement") {
        const key = "count" in next ? "count" : ("likes" in next ? "likes" : Object.keys(next)[0] || "count");
        const curr = typeof next[key] === "number" ? next[key] : parseInt(next[key] || 0, 10);
        next[key] = isNaN(curr) ? 0 : curr - 1;
      } else if (payload && typeof payload === "object" && "value" in payload) {
        next[action] = payload.value;
      }
      return next;
    });

    // 2. Safe payload extraction
    let cleanPayload = payload;
    if (payload && payload.target && typeof payload.preventDefault === "function") {
      cleanPayload = { value: payload.target.value };
    }

    // 3. Send over WebSocket if available
    const isOpen = wsRef.current && (wsRef.current.readyState === 1 || wsRef.current.readyState === (window.WebSocket?.OPEN ?? 1));
    if (isOpen) {
      wsRef.current.send(JSON.stringify({ name, payload: cleanPayload }));
    } else {
      console.warn("[Xania] WebSocket reconnecting/pending. Optimistic UI updated, will sync on reconnect:", name);
    }
  }, []);

  return (
    <StateContext.Provider value={{ state, sendEvent, connected }}>
      {children}
    </StateContext.Provider>
  );
}

export function useXaniaState() {
  return useContext(StateContext);
}
