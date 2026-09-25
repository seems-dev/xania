from __future__ import annotations

from typing import Any

from xania.renderer.component import Component
from xania.renderer.elements import Button, Div, H1, Span
from xania.renderer.state import State


class Counter(Component):
    def initial_state(self) -> dict[str, Any]:
        return {"count": 0}

    def render(self, state: State):
        count = int(state.count)
        color = (
            "text-green-400"
            if count > 0
            else "text-red-400"
            if count < 0
            else "text-white"
        )
        return Div(
            H1("Counter", class_name="text-2xl font-black text-white mb-6"),
            Span(str(count), class_name=f"text-6xl font-black {color} block mb-8"),
            Div(
                Button("−", class_name="bg-red-600 text-white px-6 py-3 rounded-xl text-xl font-bold cursor-pointer border-0 hover:bg-red-500",
                       onclick=self.on_decrement),
                Button("Reset", class_name="bg-gray-700 text-white px-6 py-3 rounded-xl text-xl font-bold cursor-pointer border-0",
                       onclick=self.on_reset),
                Button("+", class_name="bg-green-600 text-white px-6 py-3 rounded-xl text-xl font-bold cursor-pointer border-0 hover:bg-green-500",
                       onclick=self.on_increment),
                class_name="flex gap-4 justify-center"
            ),
            class_name="flex flex-col items-center justify-center min-h-screen bg-gray-950"
        )

    def on_increment(self, state: State, payload: dict[str, Any]) -> None:
        state.count += 1

    def on_decrement(self, state: State, payload: dict[str, Any]) -> None:
        state.count -= 1

    def on_reset(self, state: State, payload: dict[str, Any]) -> None:
        state.count = 0


__all__ = ["Counter"]

