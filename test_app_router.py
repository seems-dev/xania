import pytest
from fastapi.testclient import TestClient
from app import app
import re

client = TestClient(app)

def mount_component(path: str):
    # 1. Get HTML shell
    response = client.get(path)
    assert response.status_code == 200
    html = response.text
    
    # 2. Extract component name from data-component attribute
    match = re.search(r'data-component="([^"]+)"', html)
    assert match is not None
    component_name = match.group(1)
    
    # 3. Simulate client mounting via /ws
    with client.websocket_connect("/ws", cookies=response.cookies) as websocket:
        websocket.send_json({
            "component": component_name,
            "action": "__mount__",
            "payload": {}
        })
        event_res = websocket.receive_json()
        return event_res["updates"][0]["html"]

def test_app_router_home():
    html = mount_component("/")
    # Should contain layout navbar
    assert "Home" in html
    assert "About" in html
    assert "User 123" in html
    # Should contain page content
    assert "Welcome to Xania App Router!" in html
    # Should contain counter component
    assert "Counter" in html

def test_app_router_about():
    html = mount_component("/about")
    # Should contain layout navbar
    assert "Home" in html
    assert "About" in html
    # Should contain about page content
    assert "About Us" in html
    assert "We are building the future of Python web frameworks." in html

def test_app_router_dynamic():
    html = mount_component("/users/123")
    # Should contain layout navbar
    assert "Home" in html
    # Should contain dynamic content
    assert "User Profile: 123" in html

if __name__ == "__main__":
    pytest.main(["-v", __file__])
