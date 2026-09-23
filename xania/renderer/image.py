from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any
from xania.renderer.elements import Element, VoidElement

class XaniaImage:
    def __new__(cls, src: str, alt: str = "", width: int | None = None, height: int | None = None, lazy: bool = True, quality: int = 80, **attrs: Any) -> Element:
        # In dev mode, we just output an img tag pointing to the lazy endpoint
        img_attrs = {
            "src": f"/_xania/image?src={src}&fmt=webp&q={quality}",
            "alt": alt,
        }
        if width is not None:
            img_attrs["width"] = str(width)
            img_attrs["src"] += f"&w={width}"
        if height is not None:
            img_attrs["height"] = str(height)
            
        if lazy:
            img_attrs["loading"] = "lazy"
            img_attrs["decoding"] = "async"
            
        img_attrs.update(attrs)
        
        # Build mode will hook into this and replace the output with a <picture> element
        # containing generated srcset, but for now we just return the dev mode proxy tag.
        return VoidElement("img", **img_attrs)
