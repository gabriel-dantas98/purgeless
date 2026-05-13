type Props = {
  visible: boolean;
  label: string;
  pct?: number;
};

export function ProgressOverlay({ visible, label, pct }: Props) {
  if (!visible) return null;
  return (
    <div className="progress-overlay">
      <div className="progress-card">
        <div className="progress-label">{label}</div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: pct != null ? `${(pct * 100).toFixed(0)}%` : "100%" }}
          />
        </div>
        {pct != null && <div className="progress-pct">{(pct * 100).toFixed(0)}%</div>}
      </div>
    </div>
  );
}
