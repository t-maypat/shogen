import { useState } from "react";
import {
  ArrowRight,
  Check,
  ChevronRight,
  CircleDollarSign,
  Clock3,
  Info,
  Mail,
  Megaphone,
  Play,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  X,
} from "lucide-react";
import { demoBrief, kpis } from "../../data/demo";
import type { CampaignBrief, CampaignStatus } from "../../types";

interface BriefTabProps {
  status: CampaignStatus;
  onRunReplay: () => void;
}

const channelMeta = [
  { icon: Search, label: "Google Search", detail: "High-intent discovery" },
  { icon: Megaphone, label: "LinkedIn", detail: "Professional consideration" },
  { icon: Mail, label: "Email", detail: "Nurture and conversion" },
];

export function BriefTab({ status, onRunReplay }: BriefTabProps) {
  const [brief, setBrief] = useState<CampaignBrief>(demoBrief);
  const [localKpis, setLocalKpis] = useState(kpis);

  const setField = <K extends keyof CampaignBrief>(
    key: K,
    value: CampaignBrief[K],
  ) => setBrief((current) => ({ ...current, [key]: value }));

  const removeChip = (
    key: "brandVoice" | "requiredClaims" | "riskyClaims",
    value: string,
  ) =>
    setField(
      key,
      brief[key].filter((chip) => chip !== value),
    );

  const running = status === "running" || status === "evaluating";

  return (
    <div className="page page-brief">
      <section className="page-heading heading-with-action">
        <div>
          <div className="breadcrumb">
            <span>Campaigns</span>
            <ChevronRight size={13} />
            NestWise · Summer acquisition
          </div>
          <h1>Build the campaign brief</h1>
          <p>
            Commit the audience, message boundaries, and measures of success
            before Shogun generates anything.
          </p>
        </div>
        <div className="heading-note">
          <ShieldCheck size={17} />
          <span>
            <strong>Human-controlled</strong>Nothing moves beyond review without
            your approval.
          </span>
        </div>
      </section>

      <div className="brief-layout">
        <div className="brief-form-column">
          <section className="panel form-section">
            <div className="section-title-row">
              <div>
                <span className="section-index">01</span>
                <div>
                  <h2>Campaign fundamentals</h2>
                  <p>What are we bringing to market?</p>
                </div>
              </div>
              <span className="section-state">
                <Check size={12} /> Complete
              </span>
            </div>
            <div className="form-grid">
              <label className="field field-wide">
                <span>Campaign name</span>
                <input
                  value={brief.campaignName}
                  onChange={(event) =>
                    setField("campaignName", event.target.value)
                  }
                />
              </label>
              <label className="field">
                <span>Product name</span>
                <input
                  value={brief.productName}
                  onChange={(event) =>
                    setField("productName", event.target.value)
                  }
                />
              </label>
              <label className="field">
                <span>Product category</span>
                <input
                  value={brief.productCategory}
                  onChange={(event) =>
                    setField("productCategory", event.target.value)
                  }
                />
              </label>
              <label className="field field-wide">
                <span>Campaign objective</span>
                <textarea
                  rows={2}
                  value={brief.objective}
                  onChange={(event) =>
                    setField("objective", event.target.value)
                  }
                />
              </label>
              <label className="field field-wide">
                <span>Audience summary</span>
                <textarea
                  rows={3}
                  value={brief.audienceSummary}
                  onChange={(event) =>
                    setField("audienceSummary", event.target.value)
                  }
                />
                <small>{brief.audienceSummary.length} / 400</small>
              </label>
              <label className="field input-with-icon">
                <span>Budget range</span>
                <CircleDollarSign size={16} />
                <input
                  value={brief.budgetRange}
                  onChange={(event) =>
                    setField("budgetRange", event.target.value)
                  }
                />
              </label>
              <label className="field input-with-icon">
                <span>Duration</span>
                <Clock3 size={16} />
                <input
                  type="number"
                  value={brief.durationDays}
                  onChange={(event) =>
                    setField("durationDays", Number(event.target.value))
                  }
                />
                <em>days</em>
              </label>
            </div>
          </section>

          <section className="panel form-section">
            <div className="section-title-row">
              <div>
                <span className="section-index">02</span>
                <div>
                  <h2>Message guardrails</h2>
                  <p>Give generation a voice—and a fence.</p>
                </div>
              </div>
            </div>
            <div className="form-grid">
              <div className="field field-wide">
                <span>Brand voice</span>
                <div className="chip-input">
                  {brief.brandVoice.map((item) => (
                    <button
                      type="button"
                      className="chip neutral"
                      key={item}
                      onClick={() => removeChip("brandVoice", item)}
                    >
                      {item}
                      <X size={12} />
                    </button>
                  ))}
                  <button type="button" className="chip-add">
                    <Plus size={13} /> Add tone
                  </button>
                </div>
              </div>
              <div className="field">
                <span>Required claims</span>
                <div className="chip-input tall">
                  {brief.requiredClaims.map((item) => (
                    <button
                      type="button"
                      className="chip success"
                      key={item}
                      onClick={() => removeChip("requiredClaims", item)}
                    >
                      <Check size={11} />
                      {item}
                      <X size={11} />
                    </button>
                  ))}
                </div>
              </div>
              <div className="field">
                <span>
                  Claims to avoid <Info size={13} />
                </span>
                <div className="chip-input tall danger-zone">
                  {brief.riskyClaims.map((item) => (
                    <button
                      type="button"
                      className="chip danger"
                      key={item}
                      onClick={() => removeChip("riskyClaims", item)}
                    >
                      {item}
                      <X size={11} />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="panel form-section">
            <div className="section-title-row">
              <div>
                <span className="section-index">03</span>
                <div>
                  <h2>Measures of success</h2>
                  <p>Directional targets committed before generation.</p>
                </div>
              </div>
              <span className="locked-label">3 KPI limit</span>
            </div>
            <div className="kpi-editor">
              {localKpis.map((kpi, index) => (
                <div className="kpi-row" key={kpi.id}>
                  <span className="kpi-number">0{index + 1}</span>
                  <div>
                    <label>Measure</label>
                    <input
                      value={kpi.name}
                      onChange={(event) =>
                        setLocalKpis((items) =>
                          items.map((item) =>
                            item.id === kpi.id
                              ? { ...item, name: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                  </div>
                  <div>
                    <label>Signal</label>
                    <input
                      value={kpi.measurement}
                      onChange={(event) =>
                        setLocalKpis((items) =>
                          items.map((item) =>
                            item.id === kpi.id
                              ? { ...item, measurement: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                  </div>
                  <div>
                    <label>Target</label>
                    <input
                      value={kpi.target}
                      onChange={(event) =>
                        setLocalKpis((items) =>
                          items.map((item) =>
                            item.id === kpi.id
                              ? { ...item, target: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <aside className="brief-aside">
          <section className="panel launch-panel">
            <div className="launch-header">
              <div className="launch-icon">
                <Sparkles size={19} />
              </div>
              <div>
                <span className="eyebrow">Golden path</span>
                <h2>Ready to orchestrate</h2>
              </div>
            </div>
            <p className="launch-copy">
              Shogun will turn this brief into a connected, reviewable campaign
              plan.
            </p>
            <div className="run-specs">
              <div>
                <strong>3</strong>
                <span>personas</span>
              </div>
              <div>
                <strong>9</strong>
                <span>variants</span>
              </div>
              <div>
                <strong>10</strong>
                <span>stages</span>
              </div>
            </div>
            <div className="run-path">
              {[
                "Strategy and personas",
                "Connected journey",
                "Creative generation",
                "Policy-readiness",
                "Human approval",
              ].map((item, index) => (
                <div key={item}>
                  <span>{index + 1}</span>
                  <p>{item}</p>
                  {index < 4 && <i />}
                </div>
              ))}
            </div>
            <button
              type="button"
              className="primary-button launch-button"
              disabled={running}
              onClick={onRunReplay}
            >
              {running ? (
                <>
                  <span className="button-spinner" /> Workflow running
                </>
              ) : (
                <>
                  <Play size={16} fill="currentColor" /> Start replay run
                </>
              )}
              <ArrowRight size={16} />
            </button>
            <button
              type="button"
              className="secondary-button live-button"
              title="Connect VITE_API_BASE_URL to enable a live run"
            >
              <span className="live-dot" /> Start live run{" "}
              <span className="api-required">API required</span>
            </button>
            <p className="replay-note">
              <Info size={13} /> Replay uses cached, schema-valid outputs and
              the production event sequence.
            </p>
          </section>

          <section className="panel channel-panel">
            <div className="compact-panel-heading">
              <div>
                <span className="eyebrow">Fixed scope</span>
                <h3>Connected channels</h3>
              </div>
              <span className="locked-label">Locked</span>
            </div>
            {channelMeta.map(({ icon: Icon, label, detail }) => (
              <div className="channel-row" key={label}>
                <span>
                  <Icon size={16} />
                </span>
                <div>
                  <strong>{label}</strong>
                  <p>{detail}</p>
                </div>
                <Check size={15} />
              </div>
            ))}
          </section>

          <section className="aside-tip">
            <Target size={17} />
            <div>
              <strong>Why commit KPIs now?</strong>
              <p>
                Wave 2 can explain what changed against goals you chose before
                seeing the creative.
              </p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
