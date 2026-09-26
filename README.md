<div align="center">
  <h1>⚡ Xania 4.0</h1>
  <p><strong>The Full-Stack Python SPA Framework Compiled to Vite & React.</strong></p>
  <p>Pure Python syntax. Zero JavaScript tooling. Instant 0ms client reactivity. Direct access to the entire npm ecosystem.</p>

  <p>
    <a href="https://pypi.org/project/xania/"><img src="https://img.shields.io/pypi/v/xania?color=ec4899&label=PyPI" alt="PyPI version"></a>
    <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python Version"></a>
    <a href="https://vitejs.dev"><img src="https://img.shields.io/badge/bundler-Vite%205-646cff" alt="Vite"></a>
    <a href="https://react.dev"><img src="https://img.shields.io/badge/frontend-React%2018-61dafb" alt="React"></a>
    <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/backend-FastAPI-009688" alt="FastAPI"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  </p>
</div>

---

**Xania 4.0** is an enterprise-grade full-stack web framework that compiles declarative Python component trees into modern, high-performance **React Single Page Applications (SPAs)** served with **Vite** and powered by a **FastAPI WebSocket state engine**.

Write clean, pythonic code while unlocking the speed, responsiveness, and ecosystem of the modern frontend web.

---

## 🚀 Key Architectural Pillars

- **⚡ Compiled Vite + React SPA:** Your Python component definitions evaluate once into clean React JSX modules. Enjoy sub-50ms **Hot Module Replacement (HMR)** and production bundles optimized with tree-shaking.
- **🎯 0ms Instant Client Reactivity:** Eliminate the 150ms–300ms server network roundtrips of legacy server-side VDOM diffing. UI updates and client transitions happen instantaneously.
- **📦 Universal npm & React Wrapping:** Wrap and use **any npm package** (Lucide icons, Radix UI, Tailwind CSS, Framer Motion, QR Code generators) in 4 lines of Python without writing any JavaScript tooling or configuration files.
- **🔄 Sparse Delta State Synchronization:** `BaseState` automatically tracks modified properties via `__setattr__`. Over persistent WebSockets, the FastAPI backend sends only dirty keys (`{"count": 1}`), saving 95% of bandwidth.
- **📂 File-Based App Routing:** Standard Next.js/Remix style file routing natively supported (`app/page.py`, `app/features/page.py`, `app/docs/page.py`) with client-side SPA navigation via `<Link>`.

---

## 📦 Installation

Install Xania using `pip` or `uv`:

```bash
pip install xania
```

> **Requirement:** Python 3.12+ and Node.js 18+ (for Vite bundling).

---

## ⚡ Quickstart

Get a production-ready reactive SPA running in 30 seconds:

```bash
# 1. Initialize a new project
xania init my_app
cd my_app

# 2. Start the dev server (FastAPI on :8000 + Vite with HMR on :3000)
xania dev
```

Open `http://localhost:3000` in your browser. Edit your Python files in `app/` and see changes reflect instantly via Vite HMR!

---

## 🛠️ The Component & Reactive State Model

Write components and server-synchronized state using 100% Python syntax:

```python
# app/page.py
from xania import BaseState, Div, H1, P, Button, Card, Badge, LucideIcon

class CounterState(BaseState):
    count: int = 0

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

def Page():
    return Div(
        Card(
            Div(
                LucideIcon("Sparkles", class_name="w-8 h-8 text-pink-500 mb-2"),
                H1("Xania 4.0 True SPA", class_name="text-3xl font-extrabold text-white"),
                P("Full-stack Python web framework with instant 0ms reactivity.", class_name="text-zinc-400 mt-2"),
                class_name="flex flex-col items-center"
            ),
            Div(
                H1(CounterState.count, class_name="text-6xl font-black text-pink-500 my-6"),
                Div(
                    Button("- Decrement", on_click=CounterState.decrement, variant="secondary", class_name="mr-3"),
                    Button("+ Increment", on_click=CounterState.increment, variant="primary"),
                    class_name="flex justify-center"
                ),
                class_name="text-center"
            ),
            class_name="max-w-md w-full p-8 bg-zinc-900 border border-zinc-800 rounded-3xl shadow-2xl"
        ),
        class_name="min-h-screen bg-zinc-950 flex items-center justify-center p-4"
    )
```

---

## 📦 Wrapping Any npm Package in 4 Lines

Want to use third-party React npm packages? Subclass `Component` and declare its library name and tag:

```python
from xania import Component, BaseState, Card, Div

# 1. Define the npm wrapper in 4 lines of Python:
class QRCode(Component):
    library = "react-qr-code"   # npm package name
    tag = "QRCode"              # Exported component name
    is_default = True           # True for default export

# 2. Use it seamlessly in your Python UI tree:
def Page():
    return Card(
        QRCode(value="https://xania.dev", size=140, class_name="p-2 bg-white rounded-xl"),
        class_name="p-6 bg-zinc-900 border border-zinc-800 rounded-2xl"
    )
```

> **Automatic Dependency Management:** When `xania dev` or `xania export` runs, Xania automatically detects new npm wrappers, adds them to `.xania/web/package.json`, and installs them via `npm install` automatically!

---

## 🚦 Reactive Control Flow Primitives

Dynamic UI elements are expressed cleanly with reactive Python helpers:

```python
from xania import cond, foreach, Badge, Div

# Conditional rendering (compiles to JS ternary)
cond(
    UserState.is_logged_in,
    Badge("Online", variant="success"),
    Badge("Offline", variant="neutral")
)

# Array iteration (compiles to JS Array.map)
foreach(
    UserState.tags,
    lambda item, index: Badge(item, variant="purple")
)
```

---

## 🌐 File-Based Routing & SPA Navigation

Xania uses the standard `app/` folder directory hierarchy:

```
my_app/
├── app/
│   ├── page.py              # Route: /
│   ├── features/
│   │   └── page.py          # Route: /features
│   ├── docs/
│   │   └── page.py          # Route: /docs
│   └── shared.py            # Shared navigation (Navbar, Footer)
└── server.py                # FastAPI WebSocket backend
```

Navigate between routes with **0ms instant SPA transitions** using `Link`:

```python
from xania import Link

Link("Features", to="/features", class_name="text-sm text-zinc-300 hover:text-white")
```

---

## 🚀 Building & Exporting for Production

To bundle your application for production deployment:

```bash
xania export
# or: xania build
```

This compiles your Python code, bundles all React/Tailwind/npm assets with Vite, and outputs optimized static chunks into `.xania/web/dist/`.

Run your production FastAPI server directly:

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

The FastAPI backend automatically mounts the compiled static SPA and powers the real-time WebSocket state connections.

---

## 💻 CLI Command Reference

| Command | Description |
| :--- | :--- |
| `xania init <app_name>` | Scaffolds a new Xania 4.0 full-stack SPA project |
| `xania dev` | Starts FastAPI backend (`:8000`) and Vite dev server (`:3000`) with instant HMR |
| `xania compile` | Compiles Python pages into `.xania/web/src/pages/` JSX components |
| `xania export` / `build` | Compiles and builds production static assets into `.xania/web/dist/` |

---

## 📄 License

Xania is open-source software released under the [MIT License](LICENSE).
