from typing import Any
from xania.renderer.component import Component
from xania.renderer.state import State
from xania.renderer.elements import Div, H1, P, Button, Section

def metadata(**kwargs):
    return {
        "title": "Animations - Xania Demo",
        "description": "60fps Alpine.js animations natively on Xania",
        "og:image": "/static/animations.png"
    }

class Page(Component):
    def initial_state(self) -> dict[str, Any]:
        return {"server_counter": 0}

    def on_increment(self, state: State, payload: dict[str, Any]) -> None:
        state.server_counter += 1

    def render(self, state: State):
        return Div(
            # Header
            Div(
                H1("Animations & WebSockets", class_name="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600"),
                P("Scroll down to see 60fps Alpine.js animations running purely on the client side, while WebSockets handle server state.", class_name="text-gray-400 mt-4 text-xl"),
                class_name="h-screen flex flex-col justify-center items-center text-center bg-gray-900"
            ),
            
            # WebSocket Counter Demo (Server-side state)
            Section(
                H1("Server WebSocket State", class_name="text-3xl font-bold mb-6 text-white"),
                P("This counter goes to the Python server over WebSockets instantly.", class_name="text-gray-400 mb-8"),
                Div(
                    Button(
                        "Increment Server Counter",
                        class_name="bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 rounded-full font-bold shadow-lg transition-transform hover:scale-105 active:scale-95",
                        onclick="App.dispatch('Route__animations', 'increment')"
                    ),
                    P(f"Server says: {state.server_counter}", class_name="text-4xl font-black text-blue-400 mt-8"),
                    class_name="flex flex-col items-center"
                ),
                class_name="min-h-screen flex flex-col justify-center items-center bg-gray-800"
            ),
            
            # Alpine.js Client Animation Demo
            Section(
                H1("Client Alpine.js Animation", class_name="text-3xl font-bold mb-6 text-white"),
                P("This section reveals itself using purely client-side JS when you scroll.", class_name="text-gray-400 mb-8"),
                
                # Alpine component
                Div(
                    Div(
                        "🎉 I faded in without Python!",
                        class_name="text-2xl font-bold bg-pink-600 text-white p-12 rounded-3xl shadow-2xl transition-all duration-1000 transform",
                        # Alpine dynamic classes binding
                        **{
                            "x-bind:class": "shown ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-24 scale-50'"
                        }
                    ),
                    # Alpine x-data
                    x_data="{ shown: false }",
                    # Trigger when element intersects with viewport
                    **{"x-intersect": "shown = true"},
                    class_name="h-64 flex items-center justify-center"
                ),
                class_name="min-h-screen flex flex-col justify-center items-center bg-gray-900"
            )
        )
