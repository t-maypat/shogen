import { Check, Clock3, ShieldCheck, Sparkles, X } from "lucide-react";
import type { WorkflowStage } from "../types";

interface ActivityPanelProps {
  open: boolean;
  stages: WorkflowStage[];
  onClose: () => void;
}

export function ActivityPanel({ open, stages, onClose }: ActivityPanelProps) {
  return (
    <div className={`activity-overlay ${open ? "open" : ""}`} aria-hidden={!open}>
      <button className="activity-scrim" onClick={onClose} aria-label="Close activity" />
      <aside className="activity-panel">
        <div className="activity-header">
          <div><span className="eyebrow">Workflow log</span><h2>Campaign activity</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>
        <div className="activity-list">
          {[...stages].reverse().map((stage) => (
            <div className="activity-item" key={stage.id}>
              <div className={`activity-icon ${stage.status}`}>
                {stage.status === "completed" ? <Check size={14} /> : stage.status === "running" ? <Sparkles size={14} /> : stage.status === "warning" ? <ShieldCheck size={14} /> : <Clock3 size={14} />}
              </div>
              <div><strong>{stage.label}</strong><p>{stage.summary}</p></div>
              <time>{stage.status === "pending" ? "—" : "now"}</time>
            </div>
          ))}
        </div>
        <div className="activity-footnote">Events are replayed locally using the same stage contract as the production SSE stream.</div>
      </aside>
    </div>
  );
}
