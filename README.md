<div align="center">
  <h1 align="center">Xania</h1>
  <p align="center"><strong>The revolutionary Python UI framework for building blazing-fast Single Page Applications (SPAs).</strong></p>
  <p align="center">No JavaScript. No React. Just pure Python.</p>
</div>

---

Xania allows you to build modern, interactive, and highly performant web applications using a native Python component model. It combines **Server-Side Rendering (SSR)** for flawless SEO with **Persistent WebSockets** for real-time reactivity, all while automatically functioning as a seamless Single Page Application (SPA).

## 🚀 Key Capabilities

- **100% Python Frontend:** Write your components, routing, and state entirely in Python.
- **File-System App Router:** Next.js style routing natively built-in (`app/layout.py`, `app/state/page.py`).
- **Surgical DOM Diffing:** State updates execute in Python, calculate a Virtual DOM diff, and stream microscopic patches back to the browser in milliseconds over WebSockets.
- **Zero Page Reloads (SPA):** Xania automatically intercepts link clicks and performs background HTML swaps, creating a fluid SPA experience without massive JavaScript bundles.
- **Tailwind & Alpine.js Built-in:** Style your components beautifully with standard TailwindCSS classes out of the box.

---

## 📦 Installation

Xania is published on PyPI. Install it using `pip` or `uv`:

```bash
pip install xania
```

> **Note:** Xania requires Python 3.12 or newer.

---

## ⚡ Quick Start

Xania provides a CLI to instantly scaffold a new project!

```bash
# 1. Initialize a new Xania app
xania init my_app
cd my_app

# 2. Run the development server
python app.py
```

Open your browser to `http://127.0.0.1:8000` and watch your app come alive!

---

## 🏗️ How it Works: The App Router

Xania uses directory-based routing. The structure of your `app/` folder dictates the URLs of your website.

```
app/
├── layout.py         # The root layout wrapper (Navbar, Sidebar, etc)
├── page.py           # Maps to `http://localhost:8000/`
└── dashboard/
    └── page.py       # Maps to `http://localhost:8000/dashboard`
```

### Writing a Component (`app/page.py`)

Components are written as simple Python classes that inherit from `Component`.

```python
from xania.renderer.component import Component
from xania.renderer.elements import Div, H1, P, Button
from xania.renderer.state import State
from typing import Any

class Page(Component):
    # 1. Define Initial State
    def initial_state(self) -> dict[str, Any]:
        return {"counter": 0}

    # 2. Handle State Updates (Runs securely on the Python server)
    def on_increment(self, state: State, payload: dict[str, Any]) -> None:
        state.counter += 1

    # 3. Render the UI
    def render(self, state: State):
        return Div(
            H1("Welcome to Xania!", class_name="text-4xl font-bold text-blue-500"),
            P(f"Current count: {state.counter}", class_name="text-xl mt-4"),
            Button(
                "Click Me!", 
                onclick=self.action("increment"), # Binds to on_increment()
                class_name="bg-blue-600 text-white px-4 py-2 rounded-lg mt-4 cursor-pointer hover:bg-blue-500"
            ),
            class_name="p-12 min-h-screen bg-gray-950"
        )
```

## 🔄 Real-time Reactive State

When you click the button in the example above:
1. The browser sends a tiny WebSocket message: `{"action": "increment"}`.
2. Xania executes `on_increment` in Python.
3. Xania compares the old UI state with the new UI state using a lightning-fast Virtual DOM Differ.
4. It streams a tiny patch (e.g., `Update text node #2 to "1"`) back to the browser.
5. The DOM updates instantly without a page reload, preserving input focus and scroll positions.

## 🔗 SPA Navigation

Navigating between pages in Xania is completely seamless. You can use standard anchor tags:
```python
from xania.renderer.elements import A

A("Go to Dashboard", href="/dashboard", class_name="text-blue-400")
```
Xania's frontend runtime automatically intercepts the click, fetches the new `/dashboard` component via HTTP, and surgically swaps the DOM. This provides the speed of a Single Page Application without the complexity of frontend JavaScript routers!
