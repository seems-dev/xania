from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EventRequest(BaseModel):
    component: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)
    state: Optional[Dict[str, Any]] = None  # Client-owned state (cookie mode)


class Update(BaseModel):
    id: str = Field(..., min_length=1)
    html: Optional[str] = None      # Full HTML (first render / fallback)
    patches: Optional[list] = None  # Granular patches (subsequent renders)
    state: Optional[Dict[str, Any]] = None  # Updated state to store client-side


class EventResponse(BaseModel):
    updates: List[Update]


__all__ = ["EventRequest", "Update", "EventResponse"]

