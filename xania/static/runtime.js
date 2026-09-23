// static/runtime.js
//
// Minimal client runtime: mounts components and dispatches events.
// No frameworks, no eval, no inline JS required.

(function () {
  const App = {};
  const localHandlers = {};

  function serverEventsEnabled() {
    return Boolean(window.XaniaConfig && window.XaniaConfig.serverEvents === true);
  }

  let ws = null;
  let isReconnecting = false;
  let disconnectedAt = 0;
  
  function connectWebSocket() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${location.host}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[Xania] WebSocket connected");
      if (isReconnecting) {
        const downtime = Date.now() - disconnectedAt;
        // Only reload if the server was actually down for >2s (real restart)
        // Brief disconnects (event handler errors) should NOT cause a reload
        if (downtime > 2000) {
          console.log("[FastRefresh] Server restarted. Reloading page...");
          location.reload();
        } else {
          console.log("[Xania] WebSocket recovered from brief disconnect");
        }
      }
      isReconnecting = false;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.error) {
          console.warn("[Xania] Server error:", data.error);
          return;
        }
        if (data.updates) {
          App.applyUpdates(data.updates);
        }
      } catch (err) {
        console.error("Failed to parse WS message", err);
      }
    };

    ws.onclose = () => {
      if (!isReconnecting) {
        console.warn("[Xania] WebSocket closed. Reconnecting...");
        isReconnecting = true;
        disconnectedAt = Date.now();
      }
      setTimeout(connectWebSocket, 500);
    };
    
    ws.onerror = () => {
      ws.close();
    };
  }

  function navigatePath(root, path) {
    let curr = root;
    for (let i = 0; i < path.length; i++) {
      if (!curr) return null;
      curr = curr.childNodes[path[i]];
    }
    return curr;
  }

  const pendingOptimistic = new Map(); // element -> rollback snapshot

  function applyPatches(root, patches) {
    for (const p of patches) {
      const target = navigatePath(root, p.path);
      if (!target) continue;
      
      switch (p.type) {
        case "replace": {
          if (p.path.length === 0) {
            // Root-level replace: update innerHTML to preserve the mount point
            root.innerHTML = p.value || "";
          } else {
            const t = document.createElement("template");
            t.innerHTML = p.value || "";
            target.replaceWith(t.content);
          }
          break;
        }
        case "update_text":
          target.textContent = p.value || "";
          break;
        case "update_attrs":
          for (const key in p.value) {
            if (p.value[key] === null || p.value[key] === false) {
              target.removeAttribute(key);
            } else if (p.value[key] === true) {
              target.setAttribute(key, "");
            } else {
              if (key === "value" && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) {
                if (target.value !== String(p.value[key])) {
                  target.value = p.value[key];
                }
              } else {
                target.setAttribute(key, p.value[key]);
              }
            }
          }
          break;
        case "update_classes":
          if (p.value.remove && p.value.remove.length > 0) {
            target.classList.remove(...p.value.remove);
          }
          if (p.value.add && p.value.add.length > 0) {
            target.classList.add(...p.value.add);
          }
          break;
        case "insert": {
          const t = document.createElement("template");
          t.innerHTML = p.value || "";
          if (p.index >= target.childNodes.length) {
            target.appendChild(t.content);
          } else {
            target.insertBefore(t.content, target.childNodes[p.index]);
          }
          break;
        }
        case "remove":
          if (p.index < target.childNodes.length) {
            target.removeChild(target.childNodes[p.index]);
          }
          break;
      }
    }
  }

  function rollbackOptimistic(node) {
      const snap = pendingOptimistic.get(node);
      if (snap) {
          if (snap.html !== undefined) node.innerHTML = snap.html;
          node.className = snap.className;
      }
      if (node.dataset) {
          delete node.dataset.optimisticPending;
      }
      pendingOptimistic.delete(node);
  }

  App.applyUpdates = function applyUpdates(updates) {
    if (!Array.isArray(updates)) return;
    for (const u of updates) {
      if (!u || !u.id) continue;
      const el = document.getElementById(u.id);
      if (!el) continue;
      
      // Rollback optimistic UI before resolving paths for patches
      const pendingElements = el.querySelectorAll("[data-optimistic-pending]");
      if (el.dataset && el.dataset.optimisticPending) {
          rollbackOptimistic(el);
      }
      pendingElements.forEach(rollbackOptimistic);

      if (u.patches && u.patches.length > 0) {
        applyPatches(el, u.patches);
      } else if (u.html != null) {
        el.innerHTML = u.html;
      }
    }
  };

  App.dispatch = function dispatch(component, action, payload) {
    let sourceElement = null;
    if (component instanceof Element) {
      sourceElement = component;
      const closest = component.closest("[data-component]");
      if (closest) {
        component = closest.getAttribute("data-component");
      } else {
        console.warn("No [data-component] found for element");
        return;
      }
    }

    payload = payload || {};
    if (sourceElement && (sourceElement.tagName === "INPUT" || sourceElement.tagName === "TEXTAREA" || sourceElement.tagName === "SELECT")) {
      if (sourceElement.type === "checkbox" || sourceElement.type === "radio") {
        if (payload.checked === undefined) payload.checked = sourceElement.checked;
      } else {
        if (payload.value === undefined) payload.value = sourceElement.value;
      }
    }

    const handler = localHandlers[component];
    if (handler && handler(action, payload || {}) === true) {
      return;
    }
    
    if (!serverEventsEnabled()) {
        console.warn("Server events disabled.");
        return;
    }

    if (sourceElement && sourceElement.dataset.optimistic) {
      try {
        const hint = JSON.parse(sourceElement.dataset.optimistic);
        const snapshot = {
            html: sourceElement.innerHTML,
            className: sourceElement.className,
        };
        pendingOptimistic.set(sourceElement, snapshot);
        sourceElement.dataset.optimisticPending = "true";
        
        if (hint.text) sourceElement.textContent = hint.text;
        if (hint.class_add) sourceElement.classList.add(...hint.class_add.split(" "));
        if (hint.class_remove) sourceElement.classList.remove(...hint.class_remove.split(" "));
        
        // Rollback after 5s if no server patch
        setTimeout(() => {
            if (sourceElement.dataset && sourceElement.dataset.optimisticPending) {
                rollbackOptimistic(sourceElement);
            }
        }, 5000);
      } catch (e) {
        console.error("Failed to parse optimistic hint:", e);
      }
    }

    const msg = JSON.stringify({ component, action, payload: payload || {} });
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(msg);
    } else {
      console.warn("WebSocket not open. Dropping message:", msg);
    }
  };

  App.mount = function mount() {
    const mounts = document.querySelectorAll("[data-component]");
    for (const el of mounts) {
      const component = el.getAttribute("data-component");
      if (!component) continue;
      // Fetch initial HTML for each mount point over WebSocket.
      App.dispatch(component, "__mount__", {});
    }
  };

  window.App = App;

  // Optional local (no-backend) handlers for simple demo components.
  // If a handler returns true, the network request is skipped.
  localHandlers["Counter"] = function counterLocalHandler(action, payload) {
    // Expect a single mount point with id="counter" for the demo.
    const root = document.getElementById("counter");
    if (!root) return false;

    if (action === "__mount__") {
      // Fully client-side mount to avoid any backend calls for the demo counter.
      if (root.childNodes.length > 0) return true;
      root.innerHTML = [
        '<div class="flex flex-col items-center justify-center min-h-screen bg-gray-950">',
        '  <h1 class="text-2xl font-black text-white mb-6">Counter</h1>',
        '  <span class="text-6xl font-black text-white block mb-8">0</span>',
        '  <div class="flex gap-4 justify-center">',
        '    <button class="bg-red-600 text-white px-6 py-3 rounded-xl text-xl font-bold cursor-pointer border-0 hover:bg-red-500" onclick="App.dispatch(this, \'decrement\')">−</button>',
        '    <button class="bg-gray-700 text-white px-6 py-3 rounded-xl text-xl font-bold cursor-pointer border-0" onclick="App.dispatch(this, \'reset\')">Reset</button>',
        '    <button class="bg-green-600 text-white px-6 py-3 rounded-xl text-xl font-bold cursor-pointer border-0 hover:bg-green-500" onclick="App.dispatch(this, \'increment\')">+</button>',
        "  </div>",
        "</div>",
      ].join("\n");
      return true;
    }

    const valueEl = root.querySelector("span");
    if (!valueEl) return false;

    const current = parseInt(valueEl.textContent || "0", 10) || 0;
    let next = current;
    if (action === "increment") next = current + 1;
    else if (action === "decrement") next = current - 1;
    else if (action === "reset") next = 0;
    else return false;

    valueEl.textContent = String(next);
    valueEl.classList.remove("text-green-400", "text-red-400", "text-white");
    valueEl.classList.add(next > 0 ? "text-green-400" : next < 0 ? "text-red-400" : "text-white");
    return true;
  };

  // --- SPA Router ---
  async function performSPANavigation(path) {
    try {
      const appRoot = document.getElementById("app_root");
      const currentComponent = appRoot ? appRoot.getAttribute("data-component") : "";
      
      const resp = await fetch(path, {
        headers: { 
            "X-Xania-SPA": "true",
            "X-Xania-Current-Component": currentComponent
        }
      });
      if (!resp.ok) {
        location.href = path;
        return;
      }
      const data = await resp.json();
      
      if (appRoot && data.html) {
        // If the server tells us what slot changed, swap only that slot
        if (data.slot) {
          const slotSelector = `[data-xania-slot="${data.slot}"]`;
          // Find the innermost slot with this name. Wait, querySelector finds the first (outermost).
          // We can use querySelectorAll and pick the last one (innermost).
          const slots = document.querySelectorAll(slotSelector);
          const targetSlot = slots.length > 0 ? slots[slots.length - 1] : appRoot;
          targetSlot.innerHTML = data.html;
          
          if (data.component) {
            targetSlot.setAttribute("data-component", data.component);
            // We also need to update the top-level app_root if it's different? No, app_root should always track the current page component.
            // Wait, if the page component changes, app_root should track it so next navigation knows what the current component is.
            appRoot.setAttribute("data-component", data.component);
          }
        } else {
          // Use innerHTML to preserve the mount point div itself
          appRoot.innerHTML = data.html;
          
          // Update the data-component so WebSocket events route correctly
          if (data.component) {
            appRoot.setAttribute("data-component", data.component);
          }
        }
        
        if (data.title) {
          document.title = data.title;
        }
      } else {
        location.href = path;
      }
    } catch (e) {
      console.error("[Xania] SPA navigation failed:", e);
      location.href = path;
    }
  }

  document.addEventListener("click", (e) => {
    // Intercept clicks on anchor tags
    const a = e.target.closest("a");
    if (a && a.href && a.origin === location.origin) {
      // Don't intercept links with target="_blank" or special protocols
      if (a.target === "_blank" || a.href.startsWith("javascript:") || a.href.startsWith("mailto:")) {
        return;
      }
      e.preventDefault();
      const url = new URL(a.href);
      const path = url.pathname + url.search;
      if (path !== location.pathname + location.search) {
        history.pushState({}, "", path);
        performSPANavigation(path);
      }
    }
  });

  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (form.tagName !== "FORM") return;
    e.preventDefault();
    const formData = new FormData(form);
    
    // Robust serialization: handles multi-selects, checkboxes, radio groups
    const payload = {};
    for (const [key, value] of formData.entries()) {
        if (key in payload) {
            // Multiple values for same key -> convert to array
            if (!Array.isArray(payload[key])) {
                payload[key] = [payload[key]];
            }
            payload[key].push(value);
        } else {
            payload[key] = value;
        }
    }
    
    // Handle unchecked checkboxes (they're not in FormData by default)
    form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (!(cb.name in payload)) {
            payload[cb.name] = false;
        }
    });
    
    const action = form.getAttribute("data-action") || "submit";
    // We need to pass the form element so we can resolve [data-component]
    App.dispatch(form, action, payload);
  });

  window.addEventListener("popstate", () => {
    performSPANavigation(location.pathname + location.search);
  });

  document.addEventListener("DOMContentLoaded", () => {
    connectWebSocket();
  });
})();
