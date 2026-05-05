export function ProgressBar({ value = 0, kind = "info" }) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="progress" aria-label={`Progreso ${safeValue}%`}>
      <span className={`progress-fill progress-${kind}`} style={{ width: `${safeValue}%` }} />
    </div>
  );
}
