import { Activity, Bell, ChevronDown, CircleHelp, Command, Radio, Search } from "lucide-react";
import type { CampaignStatus, TabId } from "../types";

const tabs: { id: TabId; label: string; number: string }[] = [
  { id: "brief", label: "Brief", number: "01" },
  { id: "journey", label: "Journey", number: "02" },
  { id: "creative", label: "Creative review", number: "03" },
  { id: "results", label: "Results", number: "04" },
];

const statusLabels: Record<CampaignStatus, string> = {
  draft: "Draft",
  running: "Workflow running",
  approval_required: "Approval required",
  approved: "Approved",
  evaluating: "Evaluating",
  completed: "Complete",
  failed: "Needs attention",
};

interface AppHeaderProps {
  activeTab: TabId;
  status: CampaignStatus;
  onTabChange: (tab: TabId) => void;
  onOpenActivity: () => void;
}

export function AppHeader({ activeTab, status, onTabChange, onOpenActivity }: AppHeaderProps) {
  return (
    <>
      <header className="app-header">
        <div className="brand-lockup" aria-label="Shogun home">
          <div className="brand-mark"><span>S</span></div>
          <div>
            <div className="brand-name">SHOGUN</div>
            <div className="brand-subtitle">Campaign intelligence</div>
          </div>
        </div>

        <button className="campaign-switcher" type="button">
          <span className="campaign-monogram">NW</span>
          <span><small>Active campaign</small>NestWise · Summer acquisition</span>
          <ChevronDown size={15} />
        </button>

        <div className="header-actions">
          <button className="icon-button header-search" aria-label="Search"><Search size={18} /><kbd>⌘ K</kbd></button>
          <button className="icon-button" aria-label="Help"><CircleHelp size={18} /></button>
          <button className="icon-button" aria-label="Notifications"><Bell size={18} /><span className="notification-dot" /></button>
          <button className="avatar-button" aria-label="Open profile">AM</button>
        </div>
      </header>

      <div className="workspace-bar">
        <nav className="tabs" aria-label="Campaign workspace">
          {tabs.map((tab) => (
            <button
              type="button"
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => onTabChange(tab.id)}
              aria-current={activeTab === tab.id ? "page" : undefined}
            >
              <span>{tab.number}</span>{tab.label}
            </button>
          ))}
        </nav>
        <div className="workspace-meta">
          <span className="mode-badge"><Radio size={13} /> Replay</span>
          <button className={`status-pill status-${status}`} type="button" onClick={onOpenActivity}>
            {status === "running" || status === "evaluating" ? <Activity size={13} className="spin-pulse" /> : <span className="status-dot" />}
            {statusLabels[status]}
          </button>
          <span className="saved-label"><Command size={12} /> Saved just now</span>
        </div>
      </div>
    </>
  );
}
