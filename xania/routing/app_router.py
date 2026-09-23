import importlib.util
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class RouteNode:
    path_segment: str
    layout_module: Optional[Any] = None
    page_module: Optional[Any] = None
    children: dict[str, 'RouteNode'] = field(default_factory=dict)
    
    @property
    def is_dynamic(self) -> bool:
        return self.path_segment.startswith("[") and self.path_segment.endswith("]")
        
    @property
    def fastapi_path(self) -> str:
        if self.is_dynamic:
            return "{" + self.path_segment[1:-1] + "}"
        return self.path_segment


def _load_module(file_path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scan_directory(base_path: Path, module_prefix: str = "app") -> RouteNode:
    """Scans an app/ directory and builds a RouteNode tree."""
    
    def _scan(current_path: Path, segment_name: str, prefix: str) -> RouteNode:
        node = RouteNode(path_segment=segment_name)
        
        # Load page.py if exists
        page_file = current_path / "page.py"
        if page_file.exists():
            node.page_module = _load_module(page_file, f"{prefix}.page")
            
        # Load layout.py if exists
        layout_file = current_path / "layout.py"
        if layout_file.exists():
            node.layout_module = _load_module(layout_file, f"{prefix}.layout")
            
        # Scan subdirectories
        for item in sorted(current_path.iterdir()):
            if item.is_dir() and not item.name.startswith(("_", ".")):
                child_prefix = f"{prefix}.{item.name}"
                child_node = _scan(item, item.name, child_prefix)
                # Only add if it has valid routes inside
                if _has_pages(child_node):
                    node.children[item.name] = child_node
                    
        return node
        
    def _has_pages(node: RouteNode) -> bool:
        if node.page_module is not None:
            return True
        return any(_has_pages(child) for child in node.children.values())
        
    return _scan(base_path, "", module_prefix)

__all__ = ["RouteNode", "scan_directory"]
