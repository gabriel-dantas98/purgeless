import { useState } from "react";
import { DropZone } from "./components/DropZone";
import { ActionBar } from "./components/ActionBar";
import { sidecar, type MeshInfo, type SegmentResult } from "./ipc/sidecar";
import "./styles.css";

export default function App() {
  const [path, setPath] = useState<string | null>(null);
  const [info, setInfo] = useState<MeshInfo | null>(null);
  const [seg, setSeg] = useState<SegmentResult | null>(null);
  const [status, setStatus] = useState<string>("idle");

  async function handlePath(p: string) {
    try {
      setPath(p);
      setStatus("loading mesh...");
      const i = await sidecar.loadMesh(p);
      setInfo(i);
      setSeg(null);
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
      <h1>purgeless</h1>
      <ActionBar
        onPath={handlePath}
        onSegment={handleSegment}
        onExport={handleExport}
        canSegment={!!info}
        canExport={!!seg}
      />
      <DropZone onPath={handlePath} />
      {path && <p className="path">Path: {path}</p>}
      {info && (
        <p className="path">
          {info.num_faces} faces · {info.num_vertices} verts · color: {String(info.has_color)}
        </p>
      )}
      <p className="status">{status}</p>
    </main>
  );
}
