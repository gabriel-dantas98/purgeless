import { useEffect, useReducer, useState } from "react";
import { ActionBar } from "./components/ActionBar";
import { DropZone } from "./components/DropZone";
import { Viewport, decodeGeometry } from "./components/Viewport";
import { RegionsPanel } from "./components/RegionsPanel";
import { ProgressOverlay } from "./components/ProgressOverlay";
import { sidecar, MeshInfo, onProgress, ProgressEvent } from "./ipc/sidecar";
import { emptyReducerState, regionsReducer } from "./state/regions";
import "./styles.css";

type PaintMode = "off" | "brush" | "flood";

export default function App() {
  const [path, setPath] = useState<string | null>(null);
  const [info, setInfo] = useState<MeshInfo | null>(null);
  const [geom, setGeom] = useState<{ vertices: Float32Array; faces: Uint32Array } | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [paintMode, setPaintMode] = useState<PaintMode>("off");
  const [brushRadius, setBrushRadius] = useState<number>(3);
  const [hoveredFaceId, setHoveredFaceId] = useState<number | null>(null);
  const [reducerState, dispatch] = useReducer(regionsReducer, emptyReducerState);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [aiBusy, setAiBusy] = useState(false);

  useEffect(() => {
    let cleanup: (() => void) | undefined;
    onProgress((e) => setProgress(e)).then((un) => { cleanup = un; });
    return () => cleanup?.();
  }, []);

  async function handlePath(p: string) {
    setPath(p);
    setStatus("loading...");
    const i = await sidecar.loadMesh(p);
    setInfo(i);
    const g = await sidecar.getGeometry(i.handle);
    setGeom(decodeGeometry(g));
    dispatch({ type: "load", faceRegionIds: new Array(i.num_faces).fill(0) });
    setStatus(`loaded ${i.num_faces} faces`);
  }

  async function handleSegmentGeometric() {
    if (!info) return;
    setStatus("segmenting (geometric)...");
    const s = await sidecar.segmentGeometric(info.handle);
    dispatch({ type: "load", faceRegionIds: s.face_region_ids });
    setStatus(`${s.num_regions} regions (geometric)`);
  }

  async function handleSegmentSemantic() {
    if (!info) return;
    setAiBusy(true);
    setStatus("AI segmenting...");
    setProgress({ task: "segment_semantic", pct: 0 });
    try {
      const s = await sidecar.segmentSemantic(info.handle, { num_views: 12, image_size: 512 });
      dispatch({ type: "load", faceRegionIds: s.face_region_ids });
      setStatus(`${s.num_regions} regions (AI, ${s.debug_view_count} views)`);
    } catch (e) {
      setStatus(`AI failed: ${String(e)}`);
    } finally {
      setAiBusy(false);
      setProgress(null);
    }
  }

  async function handlePaintFace(faceId: number) {
    if (!info || paintMode === "off") return;
    const current = reducerState.state.faceRegionIds;
    const active = reducerState.state.activeRegionId;
    if (paintMode === "brush") {
      const r = await sidecar.paintBrush(info.handle, current, faceId, brushRadius, active);
      dispatch({ type: "apply-region-ids", faceRegionIds: r.face_region_ids, kind: "brush" });
    } else if (paintMode === "flood") {
      const r = await sidecar.paintFlood(info.handle, current, faceId, 30.0, active);
      dispatch({ type: "apply-region-ids", faceRegionIds: r.face_region_ids, kind: "flood" });
    }
  }

  async function handleMerge(srcId: number, dstId: number) {
    const r = await sidecar.regionsMerge(reducerState.state.faceRegionIds, srcId, dstId);
    dispatch({ type: "apply-region-ids", faceRegionIds: r.face_region_ids, kind: "merge" });
  }

  async function handleExport() {
    if (!info || !path || reducerState.state.faceRegionIds.length === 0) return;
    setStatus("exporting...");
    const outDir = `${path}.parts`;
    const r = await sidecar.splitAndExport(info.handle, reducerState.state.faceRegionIds, outDir);
    setStatus(`wrote ${r.files.length} STLs to ${outDir}`);
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "[") setBrushRadius((r) => Math.max(0, r - 1));
      if (e.key === "]") setBrushRadius((r) => Math.min(50, r + 1));
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        dispatch({ type: "undo" });
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <main className="app">
      <header className="topbar">
        <h1>purgeless</h1>
        <ActionBar
          onPath={handlePath}
          onSegmentGeometric={handleSegmentGeometric}
          onSegmentSemantic={handleSegmentSemantic}
          onExport={handleExport}
          onUndo={() => dispatch({ type: "undo" })}
          paintMode={paintMode}
          setPaintMode={setPaintMode}
          brushRadius={brushRadius}
          setBrushRadius={setBrushRadius}
          canSegment={!!info}
          canExport={reducerState.state.faceRegionIds.length > 0}
          aiBusy={aiBusy}
        />
      </header>
      <div className="body">
        <Viewport
          geometry={geom}
          faceRegionIds={reducerState.state.faceRegionIds.length > 0 ? reducerState.state.faceRegionIds : null}
          paintMode={paintMode}
          brushRadius={brushRadius}
          onPaintFace={handlePaintFace}
          onHoverFace={setHoveredFaceId}
          hoveredFaceId={hoveredFaceId}
        />
        <aside className="side">
          <DropZone onPath={handlePath} />
          {path && <p className="path">Path: {path}</p>}
          {info && (
            <p className="path">
              {info.num_faces} faces · {info.num_vertices} verts
            </p>
          )}
          <RegionsPanel
            state={reducerState.state}
            onSelect={(id) => dispatch({ type: "set-active", regionId: id })}
            onMerge={handleMerge}
            onRename={(id, name) => dispatch({ type: "rename", regionId: id, name })}
            onAddRegion={() => dispatch({ type: "add-region" })}
          />
          <p className="status">{status}</p>
        </aside>
      </div>
      <ProgressOverlay
        visible={!!progress || aiBusy}
        label={progress?.task ?? "working"}
        pct={progress?.pct}
      />
    </main>
  );
}
