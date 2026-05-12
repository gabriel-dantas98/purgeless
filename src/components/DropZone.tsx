import { useCallback, useState } from "react";

type Props = { onPath: (path: string) => void };

export function DropZone({ onPath }: Props) {
  const [hover, setHover] = useState(false);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setHover(false);
      const file = e.dataTransfer.files[0];
      if (!file) return;
      // In Tauri, File objects from drop events carry a `path` property at runtime
      // even though TS doesn't know about it. Fall back to file.name (relative) for
      // browser dev mode where the real path isn't exposed.
      onPath((file as unknown as { path?: string }).path ?? file.name);
    },
    [onPath],
  );

  return (
    <div
      className={`dropzone ${hover ? "hover" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setHover(true); }}
      onDragLeave={() => setHover(false)}
      onDrop={onDrop}
    >
      Drop .stl / .3mf / .glb here
    </div>
  );
}
