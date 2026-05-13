"""JSON-RPC over stdio server."""
from __future__ import annotations
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable

METHODS: dict[str, Callable[[dict], Any]] = {}

_STDOUT = sys.stdout


def notify(method_name: str, params: dict) -> None:
    """Send a JSON-RPC notification (no id) to the client."""
    msg = {"jsonrpc": "2.0", "method": method_name, "params": params}
    _STDOUT.write(json.dumps(msg) + "\n")
    _STDOUT.flush()


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


from .segment_ai import segment_semantic as _segment_semantic
from .ai.sam2_wrapper import MockSam2, Sam2Wrapper
import os as _os


@method("segment_semantic")
def _segment_semantic_rpc(params: dict) -> dict:
    handle = params["handle"]
    num_views = int(params.get("num_views", 12))
    image_size = int(params.get("image_size", 512))
    use_mock = params.get("mock", False) or _os.environ.get("PURGELESS_MOCK_SAM") == "1"
    if use_mock:
        sam = MockSam2(num_masks=int(params.get("mock_masks", 4)))
    else:
        ckpt = _os.environ.get("PURGELESS_SAM2_CKPT")
        if not ckpt:
            return {
                "_error_hint": "no_checkpoint",
                "face_region_ids": [],
                "num_regions": 0,
                "debug_view_count": 0,
            }
        sam = Sam2Wrapper(checkpoint_path=ckpt)
    return _segment_semantic(handle, sam=sam, num_views=num_views, image_size=image_size).to_dict()


from .paint import paint_brush as _paint_brush, paint_flood as _paint_flood, regions_merge as _regions_merge


@method("paint_brush")
def _paint_brush_rpc(params: dict) -> dict:
    new_ids, touched = _paint_brush(
        params["handle"],
        list(params["current_regions"]),
        int(params["face_id"]),
        int(params["brush_radius"]),
        int(params["region_id"]),
    )
    return {"face_region_ids": new_ids, "touched": touched}


@method("paint_flood")
def _paint_flood_rpc(params: dict) -> dict:
    new_ids, touched = _paint_flood(
        params["handle"],
        list(params["current_regions"]),
        int(params["face_id"]),
        float(params["angle_tolerance_deg"]),
        int(params["region_id"]),
    )
    return {"face_region_ids": new_ids, "touched": touched}


@method("regions_merge")
def _regions_merge_rpc(params: dict) -> dict:
    return {
        "face_region_ids": _regions_merge(
            list(params["face_region_ids"]),
            int(params["src_id"]),
            int(params["dst_id"]),
        )
    }


from .ai.download import download_with_progress, default_checkpoint_path, DEFAULT_URL


@method("download_sam2")
def _download_sam2_rpc(params: dict) -> dict:
    dest = Path(params.get("dest") or default_checkpoint_path())
    url = params.get("url") or DEFAULT_URL

    def on_pct(p: float) -> None:
        notify("progress", {"task": "download_sam2", "pct": p})

    download_with_progress(source=url, dest=dest, on_progress=on_pct)
    return {"path": str(dest)}


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
    global _STDOUT
    _STDOUT = stdout
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
