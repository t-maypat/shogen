import { useEffect, useRef } from "react";
import {
  FileText,
  Sparkles,
  Route,
  PenTool,
  Shield,
  Brain,
  UserCheck,
  Rocket,
  BarChart3,
  RefreshCcw,
} from "lucide-react";

const stages = [
  {
    id: "brief",
    label: "Brief",
    eyebrow: "Input",
    icon: FileText,
    color: "bg-green/15 text-green",
  },
  {
    id: "strategy",
    label: "Strategy",
    eyebrow: "AI Assist",
    icon: Sparkles,
    color: "bg-orange/15 text-orange",
  },
  {
    id: "journey",
    label: "Journey",
    eyebrow: "Plan",
    icon: Route,
    color: "bg-green/15 text-green",
  },
  {
    id: "creative",
    label: "Creative",
    eyebrow: "Generate",
    icon: PenTool,
    color: "bg-purple/15 text-purple",
  },
  {
    id: "policy",
    label: "Policy",
    eyebrow: "Deterministic",
    icon: Shield,
    color: "bg-yellow/15 text-yellow",
  },
  {
    id: "semantic",
    label: "Semantic",
    eyebrow: "AI Assist",
    icon: Brain,
    color: "bg-purple/15 text-purple",
  },
  {
    id: "approval",
    label: "Approval",
    eyebrow: "Human Gate",
    icon: UserCheck,
    color: "bg-orange/15 text-orange",
  },
  {
    id: "deploy",
    label: "Deploy",
    eyebrow: "Preview",
    icon: Rocket,
    color: "bg-green/15 text-green",
  },
  {
    id: "evaluation",
    label: "Evaluation",
    eyebrow: "Synthetic",
    icon: BarChart3,
    color: "bg-purple/15 text-purple",
  },
  {
    id: "wave2",
    label: "Wave 2",
    eyebrow: "Adapt",
    icon: RefreshCcw,
    color: "bg-orange/15 text-orange",
  },
];

export function WorkflowSection() {
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -30px 0px" },
    );

    const items = sectionRef.current?.querySelectorAll(".reveal");
    items?.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <section
      id="workflow"
      ref={sectionRef}
      className="bg-paper-deep py-24 sm:py-32"
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section header */}
        <div className="reveal mx-auto max-w-2xl text-center">
          <span className="mb-4 inline-block text-xs font-bold uppercase tracking-[0.12em] text-orange">
            End-to-end pipeline
          </span>
          <h2 className="mb-2 font-display text-3xl font-extrabold tracking-tight text-ink sm:text-4xl lg:text-5xl">
            10 stages, zero gaps
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted">
            From your initial brief to Wave 2 optimization, every stage is
            connected, traceable, and collaborative.
          </p>
        </div>

        {/* Pipeline */}
        <div className="mt-16 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
          {stages.map((stage, index) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.id}
                className={`reveal stagger-${Math.min(index + 1, 9)} group relative`}
              >
                {/* Connector line */}
                {index < stages.length - 1 && index !== 4 && (
                  <div className="absolute -right-4 top-1/2 hidden h-px w-4 border-t-2 border-dashed border-line-dark md:block" />
                )}

                <div className="flex h-full flex-col items-center rounded-2xl border border-line bg-paper p-5 text-center shadow-[0_1px_2px_rgba(24,28,26,0.04)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_6px_20px_rgba(24,28,26,0.07)]">
                  {/* Step number */}
                  <span className="mb-3 text-[9px] font-bold uppercase tracking-[0.1em] text-muted/60">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  {/* Icon */}
                  <div
                    className={`mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl ${stage.color} transition-transform duration-300 group-hover:scale-110`}
                  >
                    <Icon size={18} />
                  </div>

                  {/* Label */}
                  <span className="text-[8px] font-bold uppercase tracking-[0.08em] text-muted">
                    {stage.eyebrow}
                  </span>
                  <span className="mt-1 font-display text-sm font-bold text-ink">
                    {stage.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Key insight */}
        <div className="reveal stagger-5 mx-auto mt-12 max-w-xl">
          <div className="flex items-start gap-4 rounded-xl border border-green-soft bg-green-soft/50 p-5">
            <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-green/10">
              <Sparkles size={16} className="text-green" />
            </div>
            <div>
              <p className="text-sm font-bold text-green-dark">
                Human-in-the-loop by design
              </p>
              <p className="mt-1 text-xs leading-relaxed text-green-dark/70">
                AI handles heavy lifting across strategy, creative, and
                evaluation. But the approval gate ensures a human always has the
                final say before deployment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
