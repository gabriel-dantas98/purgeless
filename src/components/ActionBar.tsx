import { open } from "@tauri-apps/plugin-dialog";

type Props = {
  onPath: (path: string) => void;
  onSegment: () => void;
  onExport: () => void;
  canSegment: boolean;
  canExport: boolean;
};

export function ActionBar({ onPath, onSegment, onExport, canSegment, canExport }: Props) {
  async function pickFile() {
    const path = await open({
      multiple: false,
      filters: [{ name: "Mesh", extensions: ["stl", "3mf", "glb", "obj"] }],
    });
    if (typeof path === "string") onPath(path);
  }
  return (
    <div className="actionbar">
      <button onClick={pickFile}>Open file</button>
      <button onClick={onSegment} disabled={!canSegment}>Segment</button>
      <button onClick={onExport} disabled={!canExport}>Export STLs</button>
    </div>
  );
}
