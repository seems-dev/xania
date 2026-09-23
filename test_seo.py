import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_ssr_and_metadata_animations():
    response = client.get("/animations")
    assert response.status_code == 200
    html = response.text
    
    # Check SSR: The text should be present in the raw HTML without WebSockets
    assert "Animations &amp; WebSockets" in html
    assert "Server WebSocket State" in html
    assert "🎉 I faded in without Python!" in html
    
    # Check Metadata
    assert "<title>Animations - Xania Demo</title>" in html
    assert '<meta name="description" content="60fps Alpine.js animations natively on Xania" />' in html
    assert '<meta property="og:image" content="/static/animations.png" />' in html

def test_ssr_and_metadata_theme_demo():
    response = client.get("/theme_demo")
    assert response.status_code == 200
    html = response.text
    
    # Check SSR
    assert "Context API Demo" in html
    assert "This page demonstrates React-like Context in Python." in html
    
    # Check Metadata
    assert "<title>Theme Context Demo</title>" in html
    assert '<meta name="description" content="Demonstrating React-like context in Python" />' in html

if __name__ == "__main__":
    pytest.main(["-v", __file__])
