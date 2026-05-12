import { invoke } from "@tauri-apps/api/core";

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

async function rpc<T>(method: string, params: object = {}): Promise<T> {
  return invoke<T>("rpc", { method, params });
}

export const sidecar = {
  ping: () => rpc<string>("ping"),
  loadMesh: (path: string) => rpc<MeshInfo>("load_mesh", { path }),
  segmentGeometric: (handle: string) =>
    rpc<SegmentResult>("segment_geometric", { handle }),
  splitAndExport: (handle: string, faceRegionIds: number[], outDir: string) =>
    rpc<{ files: string[] }>("split_and_export", {
      handle,
      face_region_ids: faceRegionIds,
      out_dir: outDir,
    }),
  getGeometry: (handle: string) =>
    rpc<{
      vertices_b64: string;
      faces_b64: string;
      num_vertices: number;
      num_faces: number;
    }>("get_geometry", { handle }),
};
