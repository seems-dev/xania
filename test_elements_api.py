import pytest
from xania.renderer.elements import Div, H1, Span, Button, Img, Element, VoidElement, dict_to_element
from xania.renderer.component import Component
from xania.engine.differ import diff, serialize_patches


class SampleComponent(Component):
    def initial_state(self):
        return {"count": 0}

    def on_increment(self, state, payload):
        state.count += 1

    def on_delete(self, state, payload):
        pass


def test_element_render():
    """Verify element.render() public API documented in HTML_ELEMENTS.md."""
    el = Div(H1("Hello"), Img(src="logo.png"), class_name="container")
    html = el.render()
    assert html == '<div class="container"><h1>Hello</h1><img src="logo.png" /></div>'


def test_element_render_attrs():
    """Verify element.render_attrs()."""
    el = Div(class_name="main", id="root")
    attrs_html = el.render_attrs()
    assert 'class="main"' in attrs_html
    assert 'id="root"' in attrs_html


def test_element_to_dict_and_roundtrip():
    """Verify element.to_dict() and dict_to_element() roundtrip."""
    el = Div(H1("Title"), Img(src="pic.jpg"), class_name="wrapper")
    d = el.to_dict()
    assert d["tag"] == "div"
    assert d["attrs"] == {"class": "wrapper"}
    assert len(d["children"]) == 2
    assert d["children"][0] == {"tag": "h1", "children": ["Title"]}
    assert d["children"][1] == {"tag": "img", "attrs": {"src": "pic.jpg"}, "void": True}

    roundtripped = dict_to_element(d)
    assert roundtripped.render() == el.render()


def test_alpine_attribute_normalization():
    """Verify Pythonic kwargs convert to valid Alpine.js attributes."""
    el = Div(
        "Animated",
        x_bind_class="shown ? 'opacity-100' : 'opacity-0'",
        x_transition_enter="transition ease-out duration-300",
        x_transition_enter_start="opacity-0 scale-90",
        x_data="{ shown: false }",
        x_intersect="shown = true",
        _at_click="shown = !shown",
        _at_click__prevent="submit()",
        x_on_keyup__enter="onEnter()",
    )
    rendered = el.render()
    assert 'x-bind:class="shown ? &#x27;opacity-100&#x27; : &#x27;opacity-0&#x27;"' in rendered
    assert 'x-transition:enter="transition ease-out duration-300"' in rendered
    assert 'x-transition:enter-start="opacity-0 scale-90"' in rendered
    assert 'x-data="{ shown: false }"' in rendered
    assert 'x-intersect="shown = true"' in rendered
    assert '@click="shown = !shown"' in rendered
    assert '@click.prevent="submit()"' in rendered
    assert 'x-on:keyup.enter="onEnter()"' in rendered


def test_differ_with_alpine_attributes():
    """Verify VDOM patches properly normalize Alpine attributes."""
    old = Div("A", x_bind_class="active")
    new = Div("A", x_bind_class="inactive")
    patches = diff(old, new)
    serialized = serialize_patches(patches)
    assert len(serialized) == 1
    assert serialized[0]["type"] == "update_attrs"
    assert serialized[0]["value"] == {"x-bind:class": "inactive"}


def test_callable_event_handlers():
    """Verify passing bound component methods to event handlers."""
    comp = SampleComponent("comp-1")

    # Standard onclick
    btn1 = Button("+", onclick=comp.on_increment)
    assert 'onclick="App.dispatch(this, &#x27;increment&#x27;)"' in btn1.render()

    # Alpine x-on and @ click
    btn2 = Button("+", x_on_click=comp.on_increment)
    assert 'x-on:click="App.dispatch(this, &#x27;increment&#x27;)"' in btn2.render()

    btn3 = Button("+", _at_click=comp.on_increment)
    assert '@click="App.dispatch(this, &#x27;increment&#x27;)"' in btn3.render()


def test_component_action_helper():
    """Verify Component.action() works with strings and method references, including payloads."""
    comp = SampleComponent("comp-1")

    # String action
    act_str = comp.action("increment")
    assert act_str == "App.dispatch(this,'increment')"

    # Method reference action
    act_method = comp.action(comp.on_increment)
    assert act_method == "App.dispatch(this,'increment')"

    # Method reference with payload
    act_payload = comp.action(comp.on_delete, item_id=99)
    assert act_payload == 'App.dispatch(this,\'delete\',{"item_id": 99})'


def test_lambda_event_handler_rejected():
    """Verify passing an anonymous lambda raises a clear TypeError immediately."""
    with pytest.raises(TypeError, match="Anonymous lambdas cannot be used as event handlers"):
        Button("Fail", onclick=lambda: None)
