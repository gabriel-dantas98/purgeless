"""JSON-RPC over stdio server."""
from __future__ import annotations
import json
import sys
import time
import traceback
from typing import Any, Callable

METHODS: dict[str, Callable[[dict], Any]] = {}


def log_event(event: str, **fields: Any) -> None:
    payload = " ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[purgeless-sidecar] {event} {payload}".rstrip(), file=sys.stderr, flush=True)


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


from .segment import segment_geometric as _seg_geom


@method("segment_geometric")
def _seg_geom_rpc(params: dict) -> dict:
    return _seg_geom(params["handle"]).to_dict()


from .split import split_and_export as _split


@method("split_and_export")
def _split_rpc(params: dict) -> dict:
    files = _split(
        params["handle"],
        params["face_region_ids"],
        params["out_dir"],
        params.get("region_ids"),
    )
    return {"files": files}


import base64
import numpy as np
from .types import get as _get_mesh


@method("get_geometry")
def _get_geometry_rpc(params: dict) -> dict:
    mesh = _get_mesh(params["handle"])
    verts = np.asarray(mesh.vertices, dtype=np.float32)
    faces = np.asarray(mesh.faces, dtype=np.uint32)
    return {
        "vertices_b64": base64.b64encode(verts.tobytes()).decode("ascii"),
        "faces_b64": base64.b64encode(faces.tobytes()).decode("ascii"),
        "num_vertices": int(len(verts)),
        "num_faces": int(len(faces)),
    }


def handle_request(req: dict) -> dict:
    started = time.perf_counter()
    rpc_id = req.get("id")
    name = req.get("method")
    params = req.get("params") or {}
    log_event("rpc.start", id=rpc_id, method=name)
    fn = METHODS.get(name)
    if fn is None:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event("rpc.error", id=rpc_id, method=name, code=-32601, elapsed_ms=elapsed_ms)
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {name}",
                "data": {"method": name, "elapsed_ms": elapsed_ms},
            },
        }
    try:
        result = fn(params)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event("rpc.ok", id=rpc_id, method=name, elapsed_ms=elapsed_ms)
        return {"jsonrpc": "2.0", "id": rpc_id, "result": result}
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        exc_type = type(exc).__name__
        tb = traceback.format_exc()
        log_event(
            "rpc.error",
            id=rpc_id,
            method=name,
            exception_type=exc_type,
            elapsed_ms=elapsed_ms,
        )
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {
                "code": -32000,
                "message": f"{name} failed: {exc_type}: {exc}",
                "data": {
                    "method": name,
                    "exception_type": exc_type,
                    "elapsed_ms": elapsed_ms,
                    "traceback": tb,
                },
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
            log_event("rpc.parse_error", message=str(exc))
            stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {exc}",
                    "data": {"exception_type": "JSONDecodeError"},
                },
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
