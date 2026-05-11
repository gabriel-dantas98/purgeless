import { useState } from "react";
import "./styles.css";

export default function App() {
  const [path] = useState<string | null>(null);
  return (
    <main className="app">
      <h1>purgeless</h1>
      <p className="hint">Drop a .stl / .3mf / .glb to start.</p>
      {path && <p className="path">Loaded: {path}</p>}
    </main>
  );
}
