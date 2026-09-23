from typing import Any
from xania.renderer.component import Component
from xania.renderer.state import State
from xania.renderer.elements import Div, H1, Button, P, component
from xania.renderer.context import create_context, use_context

def metadata(**kwargs):
    return {
        "title": "Theme Context Demo",
        "description": "Demonstrating React-like context in Python"
    }

# 1. Create a Context
ThemeContext = create_context("light")

# 2. A Deeply Nested Functional Component
@component
def ThemeButton(label: str):
    # Read the current theme from context! No props required!
    theme = use_context(ThemeContext)
    
    bg_color = "bg-gray-800" if theme == "dark" else "bg-blue-500"
    text_color = "text-white"
    
    return Button(
        f"{label} (Theme: {theme})",
        class_name=f"{bg_color} {text_color} px-4 py-2 rounded-lg font-bold shadow-md cursor-pointer",
        onclick="App.dispatch('Route__theme_demo', 'toggle_theme')"
    )

@component
def NestedContent():
    theme = use_context(ThemeContext)
    text_color = "text-gray-300" if theme == "dark" else "text-gray-700"
    
    return Div(
        P("This is a deeply nested component.", class_name=f"{text_color} mb-4"),
        ThemeButton(label="Toggle Theme"),
        class_name="mt-8 p-6 border rounded-xl shadow-inner",
        style="border-color: #333;" if theme == "dark" else "border-color: #ccc;"
    )


# 3. The Page Component
class Page(Component):
    def initial_state(self) -> dict[str, Any]:
        return {"theme": "dark"}

    def on_toggle_theme(self, state: State, payload: dict[str, Any]) -> None:
        state.theme = "light" if state.theme == "dark" else "dark"

    def render(self, state: State):
        bg = "bg-gray-900" if state.theme == "dark" else "bg-gray-100"
        title_color = "text-white" if state.theme == "dark" else "text-gray-900"
        
        return Div(
            H1("Context API Demo", class_name=f"text-3xl font-black {title_color} mb-2"),
            P("This page demonstrates React-like Context in Python.", class_name="text-gray-500 mb-6"),
            
            # Wrap children in the Provider to pass down the theme
            ThemeContext.Provider(
                value=state.theme,
                children=[
                    NestedContent()
                ]
            ),
            class_name=f"{bg} min-h-screen p-12 transition-colors duration-300"
        )
