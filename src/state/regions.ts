export type RegionMeta = { name: string; color: string };

export type RegionsState = {
  faceRegionIds: number[];
  regions: Map<number, RegionMeta>;
  activeRegionId: number;
};

export function regionColor(id: number): string {
  const hue = (id * 137.508) % 360;
  return `hsl(${hue.toFixed(0)} 60% 55%)`;
}

export function buildRegionMap(faceRegionIds: number[]): Map<number, RegionMeta> {
  const ids = new Set(faceRegionIds);
  const map = new Map<number, RegionMeta>();
  for (const id of Array.from(ids).sort((a, b) => a - b)) {
    map.set(id, {
      name: `region_${String(id).padStart(2, "0")}`,
      color: regionColor(id),
    });
  }
  return map;
}

export function regionFaceCount(faceRegionIds: number[], regionId: number): number {
  let n = 0;
  for (const r of faceRegionIds) if (r === regionId) n++;
  return n;
}

export function nextAvailableRegionId(faceRegionIds: number[]): number {
  if (faceRegionIds.length === 0) return 0;
  let m = 0;
  for (const r of faceRegionIds) if (r > m) m = r;
  return m + 1;
}
