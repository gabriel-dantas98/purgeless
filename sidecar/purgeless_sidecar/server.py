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


from .segment import segment_geometric as _seg_geom


@method("segment_geometric")
def _seg_geom_rpc(params: dict) -> dict:
    return _seg_geom(params["handle"]).to_dict()


from .split import split_and_export as _split


@method("split_and_export")
def _split_rpc(params: dict) -> dict:
    files = _split(params["handle"], params["face_region_ids"], params["out_dir"])
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
