from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from xania.renderer.elements import Element

@dataclass
class Patch:
    type: str
    path: list[int]
    value: Any = None
    index: int = -1

def _normalize_attr_name(name: str) -> str:
    if name == "class_name":
        return "class"
    if name == "for_":
        return "for"
    if name == "http_equiv":
        return "http-equiv"
    return name.replace("_", "-")

def serialize_patches(patches: list[Patch]) -> list[dict]:
    serialized = []
    for p in patches:
        val = p.value
        # For replace/insert, convert VDOM to HTML string for easy client instantiation
        if p.type in ("replace", "insert"):
            if isinstance(val, Element):
                from xania.engine.serializer import serialize
                val = serialize(val)
            elif val is not None:
                val = str(val)
        
        # Normalize attribute keys for update_attrs
        if p.type == "update_attrs" and isinstance(val, dict):
            normalized_val = {}
            for k, v in val.items():
                normalized_val[_normalize_attr_name(k)] = v
            val = normalized_val
            
        serialized.append({
            "type": p.type,
            "path": p.path,
            "value": val,
            "index": p.index
        })
    return serialized

def diff(old: Element | str | None, new: Element | str | None, path: list[int] = None) -> list[Patch]:
    if path is None:
        path = []

    from xania.renderer.elements import LazyElement, ProviderElement
    
    # Evaluate new lazy elements
    if isinstance(new, LazyElement):
        new = new.evaluate()
        
    if isinstance(old, LazyElement):
        old = old.evaluate()
    
    # Handle ProviderElement Context pushing for the new tree
    token = None
    if isinstance(new, ProviderElement):
        stack = new.context._var.get()
        if stack is None:
            stack = []
        new_stack = stack + [new.value]
        token = new.context._var.set(new_stack)
        
    try:
        # 1. Type change or both strings but different
        if type(old) != type(new):
            return [Patch("replace", path, new)]
            
        if isinstance(old, str) and isinstance(new, str):
            if old != new:
                return [Patch("update_text", path, new)]
            return []
            
        if old is None and new is None:
            return []
            
        # At this point, both are Elements
        if old.tag != new.tag:
            return [Patch("replace", path, new)]
            
        patches = []
        
        # 2. Diff Attributes
        attr_changes = {}
        all_keys = set(old.attrs.keys()) | set(new.attrs.keys())
        for k in all_keys:
            old_val = old.attrs.get(k)
            new_val = new.attrs.get(k)
            if old_val != new_val:
                attr_changes[k] = new_val if new_val is not None else None
                
        if attr_changes:
            patches.append(Patch("update_attrs", path, attr_changes))
            
        # 3. Diff Children
        old_len = len(old.children)
        new_len = len(new.children)
        
        min_len = min(old_len, new_len)
        for i in range(min_len):
            child_path = path + [i]
            patches.extend(diff(old.children[i], new.children[i], child_path))
            
        # Removals
        if old_len > new_len:
            for i in range(new_len, old_len):
                # Always remove the element at index new_len because elements shift left
                patches.append(Patch("remove", path, index=new_len))
                
        # Additions
        if new_len > old_len:
            for i in range(old_len, new_len):
                patches.append(Patch("insert", path, new.children[i], index=i))
                
        return patches
    finally:
        if token is not None:
            new.context._var.reset(token)

__all__ = ["Patch", "serialize_patches", "diff"]
