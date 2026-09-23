# Xania Framework: AI Agent Instructions

You are an expert AI assistant helping a user write code for the **Xania** Python UI Framework.
Xania is a revolutionary full-stack framework where Single Page Applications (SPAs) are built **entirely in Python**. 
There is no React, no JavaScript, and no templating languages. 

When generating code or answering questions about Xania, you **must** strictly adhere to the following rules and patterns.

## 1. Core Architecture
- **Server-Side Rendered (SSR) + Client-Side Reactive (CSR):** Pages render as HTML on the first load. After that, user interactions trigger WebSocket messages to the Python backend. Python mutates the state, calculates a Virtual DOM diff, and streams DOM patches back to the browser.
- **Zero JS:** You should almost never write JavaScript. UI logic runs in Python.
- **SPA Routing:** Xania handles SPA navigation natively. Using `A(href="/path")` will perform a background swap without a full page reload.

## 2. File-System Routing (App Router)
Xania uses a Next.js style file-system router.
- **`app/layout.py`**: Defines the global shell (navbars, sidebars). It must define a `Layout(children)` component function.
- **`app/page.py`**: Maps to the root URL `/`. Must define a `class Page(Component):`.
- **`app/dashboard/page.py`**: Maps to `/dashboard`.

## 3. Elements vs Components
You construct the UI using Python classes that map directly to HTML tags.

**Elements (Stateless)**
```python
from xania.renderer.elements import Div, H1, P, Button, A, Input

# Python properties map to HTML attributes. Note `class_name` instead of `class`.
my_ui = Div(
    H1("Title", class_name="text-2xl font-bold"),
    P("Paragraph text", id="my-p"),
    class_name="container"
)
```

**Components (Stateful)**
To handle state, you must inherit from `Component` and implement `render()`.
```python
from xania.renderer.component import Component
from xania.renderer.elements import Div, H1, Button
from xania.renderer.state import State
from typing import Any

class Page(Component):
    def render(self, state: State):
        return Div(H1("Hello World"))
```

## 4. State Management & Events
State is managed entirely in Python.
1. Define `initial_state()` returning a dictionary.
2. Bind events using `self.action("action_name")`.
3. Define handlers named `on_<action_name>(self, state, payload)`.

```python
class Page(Component):
    def initial_state(self) -> dict[str, Any]:
        return {"counter": 0, "text": ""}

    def on_increment(self, state: State, payload: dict[str, Any]) -> None:
        # Mutating state automatically triggers a UI re-render over WebSockets
        state.counter += 1
        
    def on_update_text(self, state: State, payload: dict[str, Any]) -> None:
        # The frontend automatically sends `value` or `checked` properties in the payload
        state.text = payload.get("value", "")

    def render(self, state: State):
        return Div(
            H1(f"Count: {state.counter}"),
            Button("Add 1", onclick=self.action("increment")),
            
            # For live inputs, bind to oninput (or onchange)
            Input(
                type="text", 
                value=state.text,
                oninput=self.action("update_text")
            ),
            P(f"You typed: {state.text}")
        )
```

## 5. Styling
Xania uses **TailwindCSS** by default. 
Do not write custom CSS files unless explicitly asked. Always use utility classes via the `class_name` parameter.
```python
Button("Click", class_name="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-xl")
```

## 6. Alpine.js Animations
For client-side animations (like dropdowns or modals that shouldn't require a server roundtrip), Xania bundles **Alpine.js**.
You can inject Alpine attributes by replacing `-` with `_` in Python kwargs.
```python
# Alpine.js syntax: x-data, x-show, x-transition
Div(
    Button("Toggle", _at_click="open = !open"),
    Div(
        "I am a dropdown",
        x_show="open",
        x_transition=True
    ),
    x_data="{ open: false }"
)
```
*(Note: Use `_at_click` instead of `@click` in Python to avoid syntax errors).*

## 7. Data Fetching
You do not need `fetch()` or `axios`. Just use standard Python libraries (`requests`, `urllib`, `httpx`) directly inside a component's state handlers.

```python
import urllib.request
import json

class Page(Component):
    def initial_state(self):
        return {"data": []}
        
    def on_load_data(self, state, payload):
        req = urllib.request.Request("https://api.example.com/data")
        with urllib.request.urlopen(req) as response:
            state.data = json.loads(response.read().decode())
```

## Summary Checklist for Generating Xania Code
- [ ] Inherited from `Component`?
- [ ] Used `class_name=` instead of `class=`?
- [ ] Bound events using `self.action("name")`?
- [ ] Handled events with `on_<name>(self, state, payload)`?
- [ ] Retrieved input values using `payload.get("value")`?
- [ ] Avoided JS/React patterns (hooks, useState, fetch)?
