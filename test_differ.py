import pytest
from xania.engine.differ import diff, Patch, serialize_patches
from xania.renderer.elements import Div, Span, H1, Element

def test_type_change():
    old = Div("Hello")
    new = Span("Hello")
    patches = diff(old, new)
    assert len(patches) == 1
    assert patches[0].type == "replace"

def test_text_change():
    old = Div("Hello")
    new = Div("World")
    patches = diff(old, new)
    assert len(patches) == 1
    assert patches[0].type == "update_text"
    assert patches[0].value == "World"
    assert patches[0].path == [0]

def test_attr_change():
    old = Div("A", class_name="foo")
    new = Div("A", class_name="bar")
    patches = diff(old, new)
    assert len(patches) == 1
    assert patches[0].type == "update_attrs"
    assert patches[0].value == {"class_name": "bar"}

def test_add_child():
    old = Div("A")
    new = Div("A", Span("B"))
    patches = diff(old, new)
    assert len(patches) == 1
    assert patches[0].type == "insert"
    assert patches[0].index == 1

def test_remove_child():
    old = Div("A", Span("B"))
    new = Div("A")
    patches = diff(old, new)
    assert len(patches) == 1
    assert patches[0].type == "remove"
    assert patches[0].index == 1

if __name__ == "__main__":
    pytest.main(["-v", __file__])
