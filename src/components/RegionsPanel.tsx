import { RegionsState, regionFaceCount } from "../state/regions";

type Props = {
  state: RegionsState;
  onSelect: (regionId: number) => void;
  onMerge: (srcId: number, dstId: number) => void;
  onRename: (regionId: number, name: string) => void;
  onAddRegion: () => void;
};

export function RegionsPanel({
  state,
  onSelect,
  onMerge,
  onRename,
  onAddRegion,
}: Props) {
  const entries = Array.from(state.regions.entries());
  return (
    <div className="regions-panel">
      <div className="regions-header">
        <span>Regions ({entries.length})</span>
        <button className="add-region" onClick={onAddRegion}>
          + new
        </button>
      </div>
      <ul className="regions-list">
        {entries.map(([id, meta]) => {
          const count = regionFaceCount(state.faceRegionIds, id);
          const isActive = id === state.activeRegionId;
          return (
            <li
              key={id}
              className={`region-row ${isActive ? "active" : ""}`}
              onClick={() => onSelect(id)}
            >
              <span
                className="swatch"
                style={{ background: meta.color }}
              />
              <input
                className="region-name"
                value={meta.name}
                onChange={(e) => onRename(id, e.target.value)}
                onClick={(e) => e.stopPropagation()}
              />
              <span className="region-count">{count}</span>
              {entries.length > 1 && (
                <select
                  className="region-merge"
                  defaultValue=""
                  onClick={(e) => e.stopPropagation()}
                  onChange={(e) => {
                    const dst = Number(e.target.value);
                    if (!Number.isNaN(dst) && dst !== id) onMerge(id, dst);
                    e.currentTarget.value = "";
                  }}
                >
                  <option value="">merge…</option>
                  {entries
                    .filter(([other]) => other !== id)
                    .map(([other, m]) => (
                      <option key={other} value={other}>
                        → {m.name}
                      </option>
                    ))}
                </select>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
