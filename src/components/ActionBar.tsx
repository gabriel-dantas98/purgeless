import { open } from "@tauri-apps/plugin-dialog";

type PaintMode = "off" | "brush" | "flood";

type Props = {
  onPath: (path: string) => void;
  onSegmentGeometric: () => void;
  onSegmentSemantic: () => void;
  onExport: () => void;
  onUndo: () => void;
  paintMode: PaintMode;
  setPaintMode: (m: PaintMode) => void;
  brushRadius: number;
  setBrushRadius: (n: number) => void;
  canSegment: boolean;
  canExport: boolean;
  aiBusy: boolean;
};

export function ActionBar({
  onPath,
  onSegmentGeometric,
  onSegmentSemantic,
  onExport,
  onUndo,
  paintMode,
  setPaintMode,
  brushRadius,
  setBrushRadius,
  canSegment,
  canExport,
  aiBusy,
}: Props) {
  async function pickFile() {
    const path = await open({
      multiple: false,
      filters: [{ name: "Mesh", extensions: ["stl", "3mf", "glb", "obj", "fbx"] }],
    });
    if (typeof path === "string") onPath(path);
  }
  return (
    <div className="actionbar">
      <button onClick={pickFile}>Open file</button>
      <button onClick={onSegmentGeometric} disabled={!canSegment}>
        Geometric
      </button>
      <button onClick={onSegmentSemantic} disabled={!canSegment || aiBusy}>
        {aiBusy ? "AI…" : "AI segment"}
      </button>
      <div className="divider" />
      <button
        className={paintMode === "brush" ? "toggle on" : "toggle"}
        onClick={() => setPaintMode(paintMode === "brush" ? "off" : "brush")}
        disabled={!canSegment}
      >
        Brush
      </button>
      <button
        className={paintMode === "flood" ? "toggle on" : "toggle"}
        onClick={() => setPaintMode(paintMode === "flood" ? "off" : "flood")}
        disabled={!canSegment}
      >
        Flood
      </button>
      {paintMode === "brush" && (
        <label className="radius">
          radius
          <input
            type="range"
            min={0}
            max={50}
            value={brushRadius}
            onChange={(e) => setBrushRadius(Number(e.target.value))}
          />
          <span>{brushRadius}</span>
        </label>
      )}
      <div className="divider" />
      <button onClick={onUndo}>Undo</button>
      <button onClick={onExport} disabled={!canExport}>
        Export STLs
      </button>
    </div>
  );
}
