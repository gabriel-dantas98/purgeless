"""JSON-RPC over stdio server."""
from __future__ import annotations
import json
import sys
import traceback
from typing import Any, Callable

METHODS: dict[str, Callable[[dict], Any]] = {}


def method(name: str):
    def decorator(fn: Callable[[dict], Any]):
        METHODS[name] = fn
        return fn
    return decorator


@method("ping")
def _ping(_params: dict) -> str:
    return "pong"


from .loader import load_mesh as _load_mesh


@method("load_mesh")
def _load_mesh_rpc(params: dict) -> dict:
    path = params["path"]
    return _load_mesh(path).to_dict()


def handle_request(req: dict) -> dict:
    rpc_id = req.get("id")
    name = req.get("method")
    params = req.get("params") or {}
    fn = METHODS.get(name)
    if fn is None:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Method not found: {name}"},
        }
    try:
        result = fn(params)
        return {"jsonrpc": "2.0", "id": rpc_id, "result": result}
    except Exception as exc:  # noqa: BLE001
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {
                "code": -32000,
                "message": str(exc),
                "data": traceback.format_exc(),
            },
        }


def serve(stdin=sys.stdin, stdout=sys.stdout) -> None:
    """Read newline-delimited JSON requests, write responses."""
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }) + "\n")
            stdout.flush()
            continue
        resp = handle_request(req)
        stdout.write(json.dumps(resp) + "\n")
        stdout.flush()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
