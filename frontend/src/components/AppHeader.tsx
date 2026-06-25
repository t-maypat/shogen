import { useState, useRef, useEffect } from "react";
import {
  Activity,
  Bell,
  ChevronDown,
  CircleHelp,
  Command,
  Radio,
  Satellite,
  Search,
} from "lucide-react";
import type { CampaignStatus, ConnectionState, TabId } from "../types";

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

const connectionLabels: Record<ConnectionState, string> = {
  live: "Live",
  reconnecting: "Reconnecting",
  error: "Disconnected",
  idle: "Idle",
};

interface AppHeaderProps {
  activeTab: TabId;
  status: CampaignStatus;
  connection?: ConnectionState;
  replayMode?: boolean;
  onTabChange: (tab: TabId) => void;
  onOpenActivity: () => void;
  onToast?: (message: string) => void;
  onCreateNewCampaign?: () => void;
}

export function AppHeader({
  activeTab,
  status,
  connection = "idle",
  replayMode,
  onTabChange,
  onOpenActivity,
  onToast,
  onCreateNewCampaign,
}: AppHeaderProps) {
  const [isSwitcherOpen, setIsSwitcherOpen] = useState(false);
  const switcherRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        switcherRef.current &&
        !switcherRef.current.contains(event.target as Node)
      ) {
        setIsSwitcherOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <>
      <header className="app-header">
        <div className="brand-lockup" aria-label="Shogun home">
          <div className="brand-mark">
            <span>S</span>
          </div>
          <div>
            <div className="brand-name">SHOGUN</div>
            <div className="brand-subtitle">Campaign intelligence</div>
          </div>
        </div>

        <div className="header-divider" />

        <div className="campaign-switcher-container" ref={switcherRef}>
          <button
            className="campaign-switcher"
            type="button"
            onClick={() => setIsSwitcherOpen(!isSwitcherOpen)}
          >
            <span className="campaign-monogram">NW</span>
            <span>
              <small>Active campaign</small>NestWise · Summer acquisition
            </span>
            <ChevronDown size={15} />
          </button>

          {isSwitcherOpen && (
            <div className="campaign-dropdown">
              <div className="dropdown-header">Recent campaigns</div>
              <button
                className="dropdown-item active"
                onClick={() => {
                  setIsSwitcherOpen(false);
                  onToast?.("Switched to NestWise");
                }}
              >
                <span className="campaign-monogram">NW</span>
                <div className="item-content">
                  <div className="item-title">
                    NestWise · Summer acquisition
                  </div>
                  <div className="item-subtitle">Updated 2 mins ago</div>
                </div>
              </button>
              <button
                className="dropdown-item"
                onClick={() => {
                  setIsSwitcherOpen(false);
                  onToast?.("Switched to Zenith Bank");
                }}
              >
                <span className="campaign-monogram">ZB</span>
                <div className="item-content">
                  <div className="item-title">Zenith Bank · Youth savings</div>
                  <div className="item-subtitle">Updated 3 days ago</div>
                </div>
              </button>
              <button
                className="dropdown-item"
                onClick={() => {
                  setIsSwitcherOpen(false);
                  onToast?.("Switched to Acme Corp");
                }}
              >
                <span className="campaign-monogram">AC</span>
                <div className="item-content">
                  <div className="item-title">Acme Corp · B2B Outreach</div>
                  <div className="item-subtitle">Updated 1 week ago</div>
                </div>
              </button>
              <div className="dropdown-divider" />
              <button
                className="dropdown-item action-item"
                onClick={() => {
                  setIsSwitcherOpen(false);
                  if (onCreateNewCampaign) {
                    onCreateNewCampaign();
                  } else {
                    onToast?.("Create new campaign clicked");
                  }
                }}
              >
                + Create new campaign
              </button>
            </div>
          )}
        </div>

        <div className="header-actions">
          <button
            className="icon-button header-search"
            aria-label="Search"
            onClick={() => onToast?.("Search dialog opened")}
          >
            <Search size={18} />
            <kbd>⌘ K</kbd>
          </button>
          <button
            className="icon-button"
            aria-label="Help"
            onClick={() => onToast?.("Help menu opened")}
          >
            <CircleHelp size={18} />
          </button>
          <button
            className="icon-button"
            aria-label="Notifications"
            onClick={() => onToast?.("Notifications opened")}
          >
            <Bell size={18} />
            <span className="notification-dot" />
          </button>
          <button
            className="avatar-button"
            aria-label="Open profile"
            onClick={() => onToast?.("User profile opened")}
          >
            AM
          </button>
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
              <span>{tab.number}</span>
              {tab.label}
            </button>
          ))}
        </nav>
        <div className="workspace-meta">
          {replayMode !== undefined && (
            <span className="mode-badge">
              {replayMode ? <Radio size={13} /> : <Satellite size={13} />}{" "}
              {replayMode ? "Replay" : "Live"}
            </span>
          )}
          <span
            className={`connection-dot connection-${connection}`}
            title={connectionLabels[connection]}
          />
          <button
            className={`status-pill status-${status}`}
            type="button"
            onClick={onOpenActivity}
          >
            {status === "running" || status === "evaluating" ? (
              <Activity size={13} className="spin-pulse" />
            ) : (
              <span className="status-dot" />
            )}
            {statusLabels[status]}
          </button>
          <span className="saved-label">
            <Command size={12} /> Saved just now
          </span>
        </div>
      </div>
    </>
  );
}
