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
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
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
    // If payload is an event object (e.g. SyntheticEvent), extract safe target value if possible
    let cleanPayload = payload;
    if (payload && payload.target && typeof payload.preventDefault === "function") {
      cleanPayload = { value: payload.target.value };
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ name, payload: cleanPayload }));
    } else {
      console.warn("[Xania] WebSocket is not connected. Queuing event or skipping:", name);
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
