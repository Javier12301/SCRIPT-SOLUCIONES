import { CloudDownload } from "lucide-react";

export function Brand({ compact = false }) {
  return (
    <div className="brand">
      <span className="brand-mark">
        <CloudDownload size={compact ? 28 : 34} aria-hidden="true" />
      </span>
      {!compact && (
        <span className="brand-text">
          Downloader<span>YT</span>
        </span>
      )}
    </div>
  );
}
