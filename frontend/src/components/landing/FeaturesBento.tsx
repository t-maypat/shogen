import { useEffect, useRef } from "react";
import {
  Sparkles,
  Route,
  PenTool,
  ShieldCheck,
  BarChart3,
  RefreshCcw,
} from "lucide-react";

const features = [
  {
    icon: Sparkles,
    title: "AI Strategy Generation",
    description:
      "Automatically synthesize audience personas, KPIs, and messaging angles from a single campaign brief.",
    accent: "text-orange",
    accentBg: "bg-orange/10",
    span: "md:col-span-2",
  },
  {
    icon: Route,
    title: "Journey Orchestration",
    description:
      "Map multi-channel touchpoints across discovery, consideration, and conversion stages with intelligent allocation.",
    accent: "text-green",
    accentBg: "bg-green/10",
    span: "md:col-span-1",
  },
  {
    icon: PenTool,
    title: "Creative Generation",
    description:
      "Generate 9 channel-specific creative variants tailored to each persona and journey stage.",
    accent: "text-purple",
    accentBg: "bg-purple/10",
    span: "md:col-span-1",
  },
  {
    icon: ShieldCheck,
    title: "Policy Compliance",
    description:
      "Dual-layer review combining deterministic rule checks with semantic AI analysis to catch risky claims before deployment.",
    accent: "text-green",
    accentBg: "bg-green/10",
    span: "md:col-span-2",
  },
  {
    icon: BarChart3,
    title: "Synthetic Evaluation",
    description:
      "Score every variant on message fit, channel fit, CTA clarity, and journey consistency with directional insights.",
    accent: "text-yellow",
    accentBg: "bg-yellow/10",
    span: " md:col-span-2",
  },
  {
    icon: RefreshCcw,
    title: "Wave 2 Optimization",
    description:
      "Automatically propose allocation shifts and creative rewrites based on evaluation scores.",
    accent: "text-orange",
    accentBg: "bg-orange/10",
    span: "md:col-span-1 md:row-span-1",
  },
];

export function FeaturesBento() {
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
      { threshold: 0.15, rootMargin: "0px 0px -50px 0px" },
    );

    const items = sectionRef.current?.querySelectorAll(".reveal");
    items?.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <section
      id="features"
      ref={sectionRef}
      className="bg-surface py-24 sm:py-32"
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section header */}
        <div className="reveal mx-auto max-w-2xl text-center">
          <span className="mb-4 inline-block text-xs font-bold uppercase tracking-[0.12em] text-green">
            Platform capabilities
          </span>
          <h2 className="mb-2 font-display text-3xl font-extrabold tracking-tight text-ink sm:text-4xl lg:text-5xl">
            Every stage, one workspace
          </h2>
          <p className="mt-8 text-base leading-relaxed text-muted">
            Shogun unifies strategy, creative, compliance, and optimization into
            a single AI-assisted pipeline — so nothing falls between the cracks.
          </p>
        </div>

        {/* Bento grid */}
        <div className="mt-16 grid gap-4 md:grid-cols-3">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className={`reveal stagger-${index + 1} group cursor-default rounded-2xl border border-line bg-paper p-7 shadow-[0_1px_2px_rgba(24,28,26,0.04),0_9px_25px_rgba(24,28,26,0.04)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(24,28,26,0.08)] ${feature.span}`}
              >
                <div
                  className={`mb-5 inline-flex h-11 w-11 items-center justify-center rounded-xl ${feature.accentBg} transition-transform duration-300 group-hover:scale-110`}
                >
                  <Icon size={20} className={feature.accent} />
                </div>
                <h3 className="mb-2 font-display text-base font-bold text-ink">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
