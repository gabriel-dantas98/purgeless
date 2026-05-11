from purgeless_sidecar.server import handle_request


def test_ping_returns_pong():
    req = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
    resp = handle_request(req)
    assert resp == {"jsonrpc": "2.0", "id": 1, "result": "pong"}


def test_unknown_method_returns_error():
    req = {"jsonrpc": "2.0", "id": 2, "method": "does_not_exist"}
    resp = handle_request(req)
    assert resp["error"]["code"] == -32601
    assert resp["id"] == 2
