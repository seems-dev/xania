# renderer/state.py

from __future__ import annotations

from typing import Any, Callable


class State:
    """
    Flat state container with persistent hook storage.

    STATE SERIALIZATION RULES:
    
    Component state MUST contain only JSON-serializable primitives:
    - str, int, float, bool, None, list, dict
    - (NO database connections, file handles, or complex class instances)
    
    Non-serializable resources should be stored as instance attributes 
    on the Component itself (self.db = ...), NOT in self.state. These 
    resources are re-established in mount() when a component is restored.

    Client-sent `state` is a dict where user keys are at top-level and hook
    values are stored under `__hooks__`.
    """

    HOOKS_KEY = "__hooks__"

    def __init__(self, **initial: Any):
        hooks = initial.pop(self.HOOKS_KEY, None)
        self._data = initial
        raw_hooks = list(hooks) if hooks is not None else []
        self._hooks = [self._deserialize_hook(h) for h in raw_hooks]
        self._hook_index = 0
        self._effects = []
        self._pending_effects: list[tuple[Callable[[], Any], Any]] = []

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or name == "HOOKS_KEY":
            object.__setattr__(self, name, value)
            return
        self._data[name] = value

    def update(self, new_data: dict[str, Any]) -> None:
        self._data.update(new_data)

    def to_dict(self) -> dict[str, Any]:
        import json
        hooks = [self._serialize_hook(h) for h in self._hooks]
        result = {**self._data, self.HOOKS_KEY: hooks}
        
        # Debug-mode validation: ensure state is JSON-serializable
        if __debug__:
            try:
                json.dumps(result)
            except TypeError as e:
                raise TypeError(
                    f"State contains non-serializable value: {e}. "
                    f"Store resources (DB connections, file handles) on the Component "
                    f"instance (self.db = ...), not in self.state. "
                    f"Use mount() to re-establish resources after deserialization."
                ) from e
                
        return result

    @staticmethod
    def _deserialize_hook(h: Any) -> Any:
        # Transport-safe representation of `useRef` values.
        if isinstance(h, dict) and h.get("__ref__") is True:
            return Ref(h.get("current"))
        return h

    @staticmethod
    def _serialize_hook(h: Any) -> Any:
        if isinstance(h, Ref):
            return {"__ref__": True, "current": h.current}
        return h

    def reset_hooks(self):
        self._hook_index = 0

    def next_hook(self):
        idx = self._hook_index
        self._hook_index += 1
        return idx
    
def useState(state: State, initial):
    idx = state.next_hook()

    if idx >= len(state._hooks):
        state._hooks.append(initial)

    def set_state(value):
        old = state._hooks[idx]
        state._hooks[idx] = value(old) if callable(value) else value

        # 🔥 trigger re-render (you must connect this)
        if hasattr(state, "_rerender"):
            state._rerender()

    return state._hooks[idx], set_state


class Ref:
    def __init__(self, value):
        self.current = value


def useRef(state: State, initial=None):
    idx = state.next_hook()

    if idx >= len(state._hooks):
        state._hooks.append(Ref(initial))

    return state._hooks[idx]


def useEffect(state: State, callback, deps=None):
    idx = state.next_hook()

    if idx >= len(state._hooks):
        state._hooks.append(deps)
        state._pending_effects.append((callback, None))
        return

    old_deps = state._hooks[idx]

    changed = (
        deps is None or
        old_deps is None or
        any(a != b for a, b in zip(deps, old_deps))
    )

    if changed:
        state._pending_effects.append((callback, old_deps))
        state._hooks[idx] = deps


def useMemo(state: State, factory, deps):
    idx = state.next_hook()

    if idx >= len(state._hooks):
        value = factory()
        state._hooks.append((value, deps))
        return value

    old_value, old_deps = state._hooks[idx]

    if any(a != b for a, b in zip(deps, old_deps)):
        value = factory()
        state._hooks[idx] = (value, deps)
        return value

    return old_value

def run_effects(state: State):
    for cb, _ in state._pending_effects:
        cb()
    state._pending_effects.clear()


def useCallback(state: State, fn, deps):
    return useMemo(state, lambda: fn, deps)


def useReducer(state: State, reducer, initial):
    idx = state.next_hook()

    if idx >= len(state._hooks):
        state._hooks.append(initial)

    def dispatch(action):
        state._hooks[idx] = reducer(state._hooks[idx], action)
        if hasattr(state, "_rerender"):
            state._rerender()

    return state._hooks[idx], dispatch