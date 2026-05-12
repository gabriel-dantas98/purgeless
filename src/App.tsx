import { useState } from "react";
import { DropZone } from "./components/DropZone";
import { ActionBar } from "./components/ActionBar";
import { Viewport, decodeGeometry } from "./components/Viewport";
import { sidecar, type MeshInfo, type SegmentResult } from "./ipc/sidecar";
import "./styles.css";

type Geometry = { vertices: Float32Array; faces: Uint32Array };

export default function App() {
  const [path, setPath] = useState<string | null>(null);
  const [info, setInfo] = useState<MeshInfo | null>(null);
  const [seg, setSeg] = useState<SegmentResult | null>(null);
  const [geom, setGeom] = useState<Geometry | null>(null);
  const [status, setStatus] = useState<string>("idle");

  async function handlePath(p: string) {
    try {
      setPath(p);
      setStatus("loading mesh...");
      const i = await sidecar.loadMesh(p);
      setInfo(i);
      setSeg(null);
      setStatus("loading geometry...");
      const g = await sidecar.getGeometry(i.handle);
      setGeom(decodeGeometry(g));
      setStatus(`loaded ${i.num_faces} faces · ${i.num_vertices} verts`);
    } catch (e) {
      setStatus(`load error: ${String(e)}`);
    }
  }

  async function handleSegment() {
    if (!info) return;
    try {
      setStatus("segmenting...");
      const s = await sidecar.segmentGeometric(info.handle);
      setSeg(s);
      setStatus(`${s.num_regions} regions`);
    } catch (e) {
      setStatus(`segment error: ${String(e)}`);
    }
  }

  async function handleExport() {
    if (!info || !seg) return;
    try {
      setStatus("exporting...");
      const outDir = `${path}.parts`;
      const r = await sidecar.splitAndExport(info.handle, seg.face_region_ids, outDir);
      setStatus(`wrote ${r.files.length} STLs to ${outDir}`);
    } catch (e) {
      setStatus(`export error: ${String(e)}`);
    }
  }

  return (
    <main className="app">
      <header className="topbar">
        <h1>purgeless</h1>
        <ActionBar
          onPath={handlePath}
          onSegment={handleSegment}
          onExport={handleExport}
          canSegment={!!info}
          canExport={!!seg}
        />
      </header>
      <div className="body">
        <Viewport geometry={geom} faceRegionIds={seg?.face_region_ids ?? null} />
        <aside className="side">
          <DropZone onPath={handlePath} />
          {path && <p className="path">Path: {path}</p>}
          {info && (
            <p className="path">
              {info.num_faces} faces · {info.num_vertices} verts
            </p>
          )}
          <p className="status">{status}</p>
        </aside>
      </div>
    </main>
  );
}
