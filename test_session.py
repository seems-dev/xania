import pytest
from fastapi.testclient import TestClient
from app import app
from xania.renderer.registry import ComponentRegistry
from xania.example.counter import Counter

client = TestClient(app)

def test_counter_isolation():
    client_a = TestClient(app)
    client_b = TestClient(app)

    # 1. Mount counter in Session A
    response_a_shell = client_a.get("/")
    cookie_a = response_a_shell.cookies.get("xania_session_id")
    assert cookie_a is not None

    with client_a.websocket_connect("/ws", cookies=response_a_shell.cookies) as ws_a:
        ws_a.send_json({
            "component": "Counter",
            "action": "__mount__",
            "payload": {}
        })
        msg_a1 = ws_a.receive_json()
        html_a = msg_a1["updates"][0]["html"]
        assert ">0<" in html_a  # Initial state is 0
        
        # 2. Mount counter in Session B
        response_b_shell = client_b.get("/")
        cookie_b = response_b_shell.cookies.get("xania_session_id")
        assert cookie_b is not None
        assert cookie_a != cookie_b  # Different sessions

        with client_b.websocket_connect("/ws", cookies=response_b_shell.cookies) as ws_b:
            ws_b.send_json({
                "component": "Counter",
                "action": "__mount__",
                "payload": {}
            })
            msg_b1 = ws_b.receive_json()
            html_b = msg_b1["updates"][0]["html"]
            assert ">0<" in html_b

        # 3. Increment Counter in Session A
        ws_a.send_json({
            "component": "Counter",
            "action": "increment",
            "payload": {}
        })
        msg_a2 = ws_a.receive_json()
        updates = msg_a2["updates"]
        assert "patches" in updates[0]
        
        # Check that state changed
        comp_a = ComponentRegistry.get("Counter", cookie_a)
        assert comp_a.state.count == 1

    # 4. Verify Session B is unaffected
    comp_b = ComponentRegistry.get("Counter", cookie_b)
    assert comp_b.state.count == 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])
