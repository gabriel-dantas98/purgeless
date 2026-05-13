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

export type SparseDiff = { faceId: number; from: number }[];

export type Operation =
  | { kind: "set-all"; prev: number[] }
  | { kind: "brush"; diff: SparseDiff }
  | { kind: "flood"; diff: SparseDiff }
  | { kind: "merge"; prev: number[] }
  | { kind: "rename"; regionId: number; prev: string }
  | { kind: "add-region"; regionId: number };

export type ReducerState = {
  state: RegionsState;
  history: Operation[];
  future: Operation[];
};

export type Action =
  | { type: "load"; faceRegionIds: number[] }
  | { type: "set-active"; regionId: number }
  | { type: "apply-region-ids"; faceRegionIds: number[]; kind: "brush" | "flood" | "merge" }
  | { type: "rename"; regionId: number; name: string }
  | { type: "add-region" }
  | { type: "undo" }
  | { type: "redo" };

export const emptyReducerState: ReducerState = {
  state: { faceRegionIds: [], regions: new Map(), activeRegionId: 0 },
  history: [],
  future: [],
};

function diff(from: number[], to: number[]): SparseDiff {
  const out: SparseDiff = [];
  for (let i = 0; i < from.length; i++) {
    if (from[i] !== to[i]) out.push({ faceId: i, from: from[i] });
  }
  return out;
}

function applyDiff(arr: number[], diff: SparseDiff, currentRegionId: number, mode: "undo" | "redo"): number[] {
  const out = arr.slice();
  for (const { faceId, from } of diff) {
    out[faceId] = mode === "undo" ? from : currentRegionId;
  }
  return out;
}

export function regionsReducer(s: ReducerState, action: Action): ReducerState {
  switch (action.type) {
    case "load": {
      return {
        state: {
          faceRegionIds: action.faceRegionIds,
          regions: buildRegionMap(action.faceRegionIds),
          activeRegionId: action.faceRegionIds[0] ?? 0,
        },
        history: [],
        future: [],
      };
    }
    case "set-active": {
      return { ...s, state: { ...s.state, activeRegionId: action.regionId } };
    }
    case "apply-region-ids": {
      const prevIds = s.state.faceRegionIds;
      const nextIds = action.faceRegionIds;
      let op: Operation;
      if (action.kind === "merge") {
        op = { kind: "merge", prev: prevIds };
      } else {
        op = { kind: action.kind, diff: diff(prevIds, nextIds) };
      }
      return {
        state: {
          faceRegionIds: nextIds,
          regions: buildRegionMap(nextIds),
          activeRegionId: s.state.activeRegionId,
        },
        history: [...s.history, op],
        future: [],
      };
    }
    case "rename": {
      const prevMeta = s.state.regions.get(action.regionId);
      if (!prevMeta) return s;
      const regions = new Map(s.state.regions);
      regions.set(action.regionId, { ...prevMeta, name: action.name });
      return {
        state: { ...s.state, regions },
        history: [...s.history, { kind: "rename", regionId: action.regionId, prev: prevMeta.name }],
        future: [],
      };
    }
    case "add-region": {
      const newId = nextAvailableRegionId(s.state.faceRegionIds);
      const regions = new Map(s.state.regions);
      regions.set(newId, { name: `region_${String(newId).padStart(2, "0")}`, color: regionColor(newId) });
      return {
        state: { ...s.state, regions, activeRegionId: newId },
        history: [...s.history, { kind: "add-region", regionId: newId }],
        future: [],
      };
    }
    case "undo": {
      const op = s.history[s.history.length - 1];
      if (!op) return s;
      const history = s.history.slice(0, -1);
      const future = [...s.future, op];
      if (op.kind === "merge" || op.kind === "set-all") {
        return {
          state: {
            faceRegionIds: op.prev,
            regions: buildRegionMap(op.prev),
            activeRegionId: s.state.activeRegionId,
          },
          history,
          future,
        };
      }
      if (op.kind === "brush" || op.kind === "flood") {
        const nextIds = applyDiff(s.state.faceRegionIds, op.diff, s.state.activeRegionId, "undo");
        return {
          state: { faceRegionIds: nextIds, regions: buildRegionMap(nextIds), activeRegionId: s.state.activeRegionId },
          history,
          future,
        };
      }
      if (op.kind === "rename") {
        const meta = s.state.regions.get(op.regionId);
        if (!meta) return s;
        const regions = new Map(s.state.regions);
        regions.set(op.regionId, { ...meta, name: op.prev });
        return { state: { ...s.state, regions }, history, future };
      }
      if (op.kind === "add-region") {
        const regions = new Map(s.state.regions);
        regions.delete(op.regionId);
        return { state: { ...s.state, regions }, history, future };
      }
      return s;
    }
    case "redo": {
      return s;
    }
    default:
      return s;
  }
}
