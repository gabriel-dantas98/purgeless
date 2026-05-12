import { useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

type Geometry = { vertices: Float32Array; faces: Uint32Array };

type Props = {
  geometry: Geometry | null;
  faceRegionIds: number[] | null;
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
}): Geometry {
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

function MeshBody({ geometry, faceRegionIds }: Props) {
  const bufferGeom = useMemo(() => {
    if (!geometry) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(geometry.vertices, 3));
    g.setIndex(new THREE.BufferAttribute(geometry.faces, 1));
    g.computeVertexNormals();

    if (faceRegionIds) {
      const expanded = g.toNonIndexed();
      const positions = expanded.getAttribute("position");
      const colors = new Float32Array(positions.count * 3);
      for (let f = 0; f < faceRegionIds.length; f++) {
        const [r, gn, b] = regionColor(faceRegionIds[f]);
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
    }
    return g;
  }, [geometry, faceRegionIds]);

  if (!bufferGeom) return null;
  return (
    <mesh geometry={bufferGeom}>
      <meshStandardMaterial
        vertexColors={!!faceRegionIds}
        color={faceRegionIds ? undefined : "#bbb"}
      />
    </mesh>
  );
}

export function Viewport({ geometry, faceRegionIds }: Props) {
  // Auto-frame camera to mesh bounds.
  const camTarget = useMemo<[number, number, number]>(() => {
    if (!geometry) return [0, 0, 0];
    const v = geometry.vertices;
    let minX = Infinity, minY = Infinity, minZ = Infinity;
    let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
    for (let i = 0; i < v.length; i += 3) {
      if (v[i] < minX) minX = v[i];
      if (v[i] > maxX) maxX = v[i];
      if (v[i + 1] < minY) minY = v[i + 1];
      if (v[i + 1] > maxY) maxY = v[i + 1];
      if (v[i + 2] < minZ) minZ = v[i + 2];
      if (v[i + 2] > maxZ) maxZ = v[i + 2];
    }
    return [(minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2];
  }, [geometry]);

  const camDistance = useMemo(() => {
    if (!geometry) return 200;
    const v = geometry.vertices;
    let minX = Infinity, minY = Infinity, minZ = Infinity;
    let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
    for (let i = 0; i < v.length; i += 3) {
      if (v[i] < minX) minX = v[i];
      if (v[i] > maxX) maxX = v[i];
      if (v[i + 1] < minY) minY = v[i + 1];
      if (v[i + 1] > maxY) maxY = v[i + 1];
      if (v[i + 2] < minZ) minZ = v[i + 2];
      if (v[i + 2] > maxZ) maxZ = v[i + 2];
    }
    const span = Math.max(maxX - minX, maxY - minY, maxZ - minZ);
    return span > 0 ? span * 2 : 200;
  }, [geometry]);

  return (
    <div className="viewport">
      <Canvas
        camera={{
          position: [camDistance, camDistance, camDistance],
          fov: 45,
          near: Math.max(camDistance * 0.001, 0.1),
          far: camDistance * 100,
        }}
      >
        <ambientLight intensity={0.4} />
        <directionalLight position={[100, 200, 100]} intensity={0.8} />
        <directionalLight position={[-100, -50, -100]} intensity={0.4} />
        <MeshBody geometry={geometry} faceRegionIds={faceRegionIds} />
        <OrbitControls makeDefault target={camTarget} />
      </Canvas>
    </div>
  );
}
