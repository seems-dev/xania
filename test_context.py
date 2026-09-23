import pytest
from xania.renderer.context import create_context, use_context
from xania.renderer.elements import Div, Span, component
from xania.engine.serializer import serialize

def test_context_default_value():
    Ctx = create_context("default_value")
    
    @component
    def Reader():
        val = use_context(Ctx)
        return Span(val)
        
    html = serialize(Reader())
    assert "<span>default_value</span>" in html

def test_context_provider():
    Ctx = create_context("default_value")
    
    @component
    def Reader():
        val = use_context(Ctx)
        return Span(val)
        
    html = serialize(
        Ctx.Provider(
            value="provided_value",
            children=[Reader()]
        )
    )
    assert "<span>provided_value</span>" in html

def test_context_nested_providers():
    Ctx = create_context("default")
    
    @component
    def Reader():
        val = use_context(Ctx)
        return Span(val)
        
    html = serialize(
        Ctx.Provider(
            value="outer",
            children=[
                Reader(), # Should read "outer"
                Ctx.Provider(
                    value="inner",
                    children=[
                        Reader() # Should read "inner"
                    ]
                )
            ]
        )
    )
    
    # Provider serializes to a div with display: contents
    assert "<span>outer</span>" in html
    assert "<span>inner</span>" in html

if __name__ == "__main__":
    pytest.main(["-v", __file__])
