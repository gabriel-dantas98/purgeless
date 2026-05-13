import { useMemo, useRef } from "react";
import { Canvas, ThreeEvent } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

type Props = {
  geometry: { vertices: Float32Array; faces: Uint32Array } | null;
  faceRegionIds: number[] | null;
  paintMode: "off" | "brush" | "flood";
  brushRadius: number;
  onPaintFace?: (faceId: number) => void;
  onHoverFace?: (faceId: number | null) => void;
  hoveredFaceId?: number | null;
};

function decode(b64: string): ArrayBuffer {
  const bin = atob(b64);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}

export function decodeGeometry(payload: {
  vertices_b64: string;
  faces_b64: string;
}) {
  return {
    vertices: new Float32Array(decode(payload.vertices_b64)),
    faces: new Uint32Array(decode(payload.faces_b64)),
  };
}

function regionColor(id: number): [number, number, number] {
  const hue = (id * 137.508) % 360;
  const c = new THREE.Color().setHSL(hue / 360, 0.6, 0.55);
  return [c.r, c.g, c.b];
}

function MeshBody({
  geometry,
  faceRegionIds,
  paintMode,
  onPaintFace,
  onHoverFace,
  hoveredFaceId,
}: Props) {
  const meshRef = useRef<THREE.Mesh>(null);
  const isPainting = useRef(false);

  const bufferGeom = useMemo(() => {
    if (!geometry) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(geometry.vertices, 3));
    g.setIndex(new THREE.BufferAttribute(geometry.faces, 1));
    g.computeVertexNormals();
    return g;
  }, [geometry]);

  const coloredGeom = useMemo(() => {
    if (!bufferGeom || !faceRegionIds) return bufferGeom;
    const expanded = bufferGeom.toNonIndexed();
    const positions = expanded.getAttribute("position");
    const colors = new Float32Array(positions.count * 3);
    for (let f = 0; f < faceRegionIds.length; f++) {
      let [r, gn, b] = regionColor(faceRegionIds[f]);
      if (hoveredFaceId === f && paintMode !== "off") {
        r = Math.min(1, r * 1.6); gn = Math.min(1, gn * 1.6); b = Math.min(1, b * 1.6);
      }
      for (let v = 0; v < 3; v++) {
        const idx = (f * 3 + v) * 3;
        colors[idx] = r;
        colors[idx + 1] = gn;
        colors[idx + 2] = b;
      }
    }
    expanded.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    expanded.computeVertexNormals();
    return expanded;
  }, [bufferGeom, faceRegionIds, hoveredFaceId, paintMode]);

  function handlePointer(e: ThreeEvent<PointerEvent>) {
    if (paintMode === "off") return;
    const idx = e.faceIndex;
    if (idx == null) return;
    onHoverFace?.(idx);
    if (isPainting.current && onPaintFace) {
      onPaintFace(idx);
    }
  }

  function handlePointerDown(e: ThreeEvent<PointerEvent>) {
    if (paintMode === "off") return;
    isPainting.current = true;
    if (e.faceIndex != null) onPaintFace?.(e.faceIndex);
  }

  function handlePointerUp() {
    isPainting.current = false;
  }

  if (!coloredGeom) return null;
  return (
    <mesh
      ref={meshRef}
      geometry={coloredGeom}
      onPointerMove={handlePointer}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerLeave={() => { isPainting.current = false; onHoverFace?.(null); }}
    >
      <meshStandardMaterial vertexColors={!!faceRegionIds} color={faceRegionIds ? undefined : "#bbb"} />
    </mesh>
  );
}

export function Viewport(props: Props) {
  const orbitEnabled = props.paintMode === "off";
  return (
    <div className={`viewport ${props.paintMode !== "off" ? "painting" : ""}`}>
      <Canvas camera={{ position: [200, 200, 200], fov: 45, near: 1, far: 5000 }}>
        <ambientLight intensity={0.4} />
        <directionalLight position={[100, 200, 100]} intensity={0.8} />
        <directionalLight position={[-100, -50, -100]} intensity={0.4} />
        <MeshBody {...props} />
        <OrbitControls makeDefault enabled={orbitEnabled} />
      </Canvas>
    </div>
  );
}
