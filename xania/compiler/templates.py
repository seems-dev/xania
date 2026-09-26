from __future__ import annotations

import json
from typing import Any, List
from xania.components.base import Var, EventHandler
from xania.components.component import Component, Fragment
from xania.components.control_flow import Cond, Foreach, Match


class RenderUtils:
    """JSX Code Generator for Xania Component trees."""

    @classmethod
    def render(cls, node: Any, depth: int = 0) -> str:
        indent = "  " * depth

        if isinstance(node, Cond):
            cond_js = node.condition.to_js()
            true_code = cls.render(node.true_view, depth + 1)
            false_code = cls.render(node.false_view, depth + 1) if node.false_view != "" else "null"
            return f"({cond_js} ? (\n{indent}  {true_code}\n{indent}) : (\n{indent}  {false_code}\n{indent}))"

        if isinstance(node, Foreach):
            iter_js = node.iterable.to_js()
            child_code = cls.render(node.rendered_child, depth + 1)
            return f"({iter_js} ?? []).map((item, index) => (\n{indent}  {child_code}\n{indent}))"

        if isinstance(node, Match):
            cond_js = node.condition.to_js()
            # Compile into nested ternary
            res = "null"
            if node.default is not None:
                res = cls.render(node.default, depth + 1)
            for val, view in reversed(node.cases):
                val_js = Var.create(val).to_js()
                view_js = cls.render(view, depth + 1)
                res = f"({cond_js} === {val_js} ? (\n{indent}  {view_js}\n{indent}) : {res})"
            return res

        if isinstance(node, Component):
            tag_name = node.alias or node.tag
            is_fragment = (tag_name == "Fragment")

            # Build props
            prop_strs: List[str] = []
            for k, v in node.props.items():
                if isinstance(v, EventHandler):
                    prop_strs.append(f"{k}={{{v.to_js()}}}")
                elif isinstance(v, Var):
                    expr = v.to_js()
                    # Check if it's a simple string literal e.g. '"btn btn-primary"'
                    if expr.startswith('"') and expr.endswith('"') and len(expr) >= 2:
                        prop_strs.append(f'{k}={expr}')
                    else:
                        prop_strs.append(f"{k}={{{expr}}}")
                elif isinstance(v, bool):
                    prop_strs.append(f"{k}={{{'true' if v else 'false'}}}")
                elif isinstance(v, (int, float)):
                    prop_strs.append(f"{k}={{{v}}}")
                elif isinstance(v, str):
                    prop_strs.append(f'{k}="{v}"')
                else:
                    prop_strs.append(f"{k}={{{json.dumps(v)}}}")

            props_joined = f" {' '.join(prop_strs)}" if prop_strs else ""

            if not node.children:
                if is_fragment:
                    return "<></>"
                return f"<{tag_name}{props_joined} />"

            # Render children
            rendered_children: List[str] = []
            for child in node.children:
                if isinstance(child, (Component, Cond, Foreach, Match)):
                    child_str = cls.render(child, depth + 1)
                    if isinstance(child, (Cond, Foreach, Match)):
                        rendered_children.append(f"{indent}  {{{child_str}}}")
                    else:
                        rendered_children.append(f"{indent}  {child_str}")
                elif isinstance(child, Var):
                    rendered_children.append(f"{indent}  {{{child.to_js()}}}")
                elif isinstance(child, (int, float)):
                    rendered_children.append(f"{indent}  {{{child}}}")
                elif child is not None:
                    # Raw string or text with JSX entity escaping
                    txt = (
                        str(child)
                        .replace("&", "&amp;")
                        .replace("{", "&#123;")
                        .replace("}", "&#125;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                    )
                    rendered_children.append(f"{indent}  {txt}")

            children_joined = "\n".join(rendered_children)
            if is_fragment:
                return f"<>\n{children_joined}\n{indent}</>"
            return f"<{tag_name}{props_joined}>\n{children_joined}\n{indent}</{tag_name}>"

        if isinstance(node, Var):
            return f"{{{node.to_js()}}}"

        return json.dumps(str(node))
