import contextvars
from typing import TypeVar, Generic, Any
from xania.renderer.elements import ProviderElement

T = TypeVar("T")

class Context(Generic[T]):
    """
    React-like Context for passing state deeply down the component tree.
    Powered by Python's thread-safe and async-safe contextvars.
    """
    def __init__(self, default_value: T):
        self.default_value = default_value
        self._var: contextvars.ContextVar[list[T]] = contextvars.ContextVar(f"context_{id(self)}", default=None)

    def get_value(self) -> T:
        """Returns the current context value."""
        stack = self._var.get()
        if stack is None or len(stack) == 0:
            return self.default_value
        return stack[-1]
        
    def Provider(self, value: T, children: Any) -> ProviderElement:
        """Returns a ProviderElement which sets the context during evaluation."""
        return ProviderElement(context=self, value=value, children=children)

def create_context(default_value: T) -> Context[T]:
    """Creates a new Context object."""
    return Context(default_value)

def use_context(context: Context[T]) -> T:
    """Reads the current value of a context."""
    return context.get_value()

__all__ = ["Context", "create_context", "use_context"]
