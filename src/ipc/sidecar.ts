import { invoke } from "@tauri-apps/api/core";
import { listen, UnlistenFn } from "@tauri-apps/api/event";

export type MeshInfo = {
  handle: string;
  num_faces: number;
  num_vertices: number;
  bbox_min: [number, number, number];
  bbox_max: [number, number, number];
  has_color: boolean;
};

export type SegmentResult = {
  face_region_ids: number[];
  num_regions: number;
};

export type SemanticSegmentResult = SegmentResult & {
  debug_view_count: number;
};

export type PaintResult = {
  face_region_ids: number[];
  touched: number;
};

async function rpc<T>(method: string, params: object = {}): Promise<T> {
  return invoke<T>("rpc", { method, params });
}

export const sidecar = {
  ping: () => rpc<string>("ping"),

  loadMesh: (path: string) => rpc<MeshInfo>("load_mesh", { path }),

  segmentGeometric: (handle: string) =>
    rpc<SegmentResult>("segment_geometric", { handle }),

  segmentSemantic: (
    handle: string,
    opts: { num_views?: number; image_size?: number; mock?: boolean } = {}
  ) => rpc<SemanticSegmentResult>("segment_semantic", { handle, ...opts }),

  paintBrush: (
    handle: string,
    currentRegions: number[],
    faceId: number,
    brushRadius: number,
    regionId: number
  ) =>
    rpc<PaintResult>("paint_brush", {
      handle,
      current_regions: currentRegions,
      face_id: faceId,
      brush_radius: brushRadius,
      region_id: regionId,
    }),

  paintFlood: (
    handle: string,
    currentRegions: number[],
    faceId: number,
    angleToleranceDeg: number,
    regionId: number
  ) =>
    rpc<PaintResult>("paint_flood", {
      handle,
      current_regions: currentRegions,
      face_id: faceId,
      angle_tolerance_deg: angleToleranceDeg,
      region_id: regionId,
    }),

  regionsMerge: (faceRegionIds: number[], srcId: number, dstId: number) =>
    rpc<{ face_region_ids: number[] }>("regions_merge", {
      face_region_ids: faceRegionIds,
      src_id: srcId,
      dst_id: dstId,
    }),

  splitAndExport: (handle: string, faceRegionIds: number[], outDir: string) =>
    rpc<{ files: string[] }>("split_and_export", {
      handle,
      face_region_ids: faceRegionIds,
      out_dir: outDir,
    }),

  downloadSam2: () => rpc<{ path: string }>("download_sam2"),

  getGeometry: (handle: string) =>
    rpc<{
      vertices_b64: string;
      faces_b64: string;
      num_vertices: number;
      num_faces: number;
    }>("get_geometry", { handle }),
};

export type ProgressEvent = { task: string; pct: number };

export async function onProgress(
  cb: (e: ProgressEvent) => void
): Promise<UnlistenFn> {
  return listen<ProgressEvent>("sidecar:progress", (evt) => cb(evt.payload));
}
