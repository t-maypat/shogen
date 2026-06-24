import { useNavigate } from "react-router-dom";
import { ArrowRight, Play } from "lucide-react";

export function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="relative min-h-screen overflow-hidden bg-header pt-16">
      {/* Background effects */}
      <div className="absolute inset-0">
        {/* Dot grid */}
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: "radial-gradient(rgba(255,255,255,0.8) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />

        {/* Orbital rings */}
        <div className="absolute -right-32 -top-32 h-[600px] w-[600px] animate-orbit rounded-full border border-white/[0.04]" />
        <div className="absolute -right-16 -top-16 h-[450px] w-[450px] animate-orbit-reverse rounded-full border border-orange/[0.08]" />
        <div className="absolute -left-48 bottom-[-200px] h-[500px] w-[500px] animate-orbit rounded-full border border-green/[0.06]" />

        {/* Gradient glow */}
        <div className="absolute left-1/2 top-1/3 h-[500px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-orange/[0.04] blur-[120px]" />
        <div className="absolute right-0 top-0 h-[400px] w-[400px] rounded-full bg-green/[0.03] blur-[100px]" />
      </div>

      {/* Content */}
      <div className="relative z-10 mx-auto flex min-h-[calc(100vh-64px)] max-w-7xl flex-col items-center justify-center px-6 text-center lg:px-8">
        {/* Badge */}
        <div
          className="animate-fade-up mb-8 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-4 py-1.5 backdrop-blur-sm"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-green animate-glow-pulse" />
          <span className="text-xs font-semibold text-white/70">
            AI-powered campaign orchestration
          </span>
        </div>

        {/* Headline */}
        <h1 className="animate-fade-up mb-6 max-w-4xl font-display text-5xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-6xl lg:text-7xl" style={{ animationDelay: "0.1s" }}>
          Orchestrate campaigns{" "}
          <span className="bg-gradient-to-r from-orange via-yellow to-orange bg-clip-text text-transparent">
            with intelligence
          </span>
        </h1>

        {/* Subtitle */}
        <p
          className="animate-fade-up mx-auto mb-10 max-w-2xl text-base leading-relaxed text-white/50 sm:text-lg"
          style={{ animationDelay: "0.2s" }}
        >
          From brief to deployment in one AI-assisted workflow. Shogun generates personas,
          crafts multi-channel creative, runs policy checks, and optimizes allocation —
          all before a single dollar is spent.
        </p>

        {/* CTAs */}
        <div
          className="animate-fade-up flex flex-col items-center gap-4 sm:flex-row"
          style={{ animationDelay: "0.3s" }}
        >
          <button
            onClick={() => navigate("/app")}
            className="group flex items-center gap-2 rounded-xl bg-orange px-7 py-3.5 text-sm font-bold text-white shadow-[0_0_30px_rgba(220,103,72,0.3)] transition-all hover:-translate-y-0.5 hover:shadow-[0_0_40px_rgba(220,103,72,0.45)]"
          >
            Launch workspace
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
          </button>
          <button className="flex items-center gap-2 rounded-xl border border-white/30 bg-white/[0.08] px-7 py-3.5 text-sm font-semibold text-white backdrop-blur-sm transition-all hover:border-white/50 hover:bg-white/[0.12]">
            <Play size={14} className="fill-current" />
            Watch demo
          </button>
        </div>

        {/* Floating UI preview */}
        <div
          className="animate-fade-up relative mt-16 w-full max-w-4xl"
          style={{ animationDelay: "0.5s" }}
        >
          <div className="animate-float rounded-2xl border border-white/[0.08] bg-white/[0.03] p-2 shadow-2xl backdrop-blur-sm">
            {/* Mock header bar */}
            <div className="flex items-center gap-3 rounded-t-xl bg-header px-4 py-3 border-b border-white/[0.06]">
              <div className="flex gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-red/60" />
                <span className="h-2.5 w-2.5 rounded-full bg-yellow/60" />
                <span className="h-2.5 w-2.5 rounded-full bg-green/60" />
              </div>
              <div className="ml-4 flex items-center gap-2">
                <div className="grid h-5 w-5 rotate-45 place-items-center rounded bg-orange">
                  <span className="-rotate-45 font-display text-[7px] font-extrabold text-white">S</span>
                </div>
                <span className="font-display text-[10px] font-bold tracking-[0.14em] text-white/70">SHOGUN</span>
              </div>
              <div className="ml-auto flex gap-6">
                {["Brief", "Journey", "Creative", "Results"].map((tab) => (
                  <span key={tab} className={`text-[10px] font-semibold ${tab === "Journey" ? "text-white" : "text-white/30"}`}>
                    {tab}
                  </span>
                ))}
              </div>
            </div>

            {/* Mock content area */}
            <div className="grid grid-cols-3 gap-3 p-4">
              {/* Mock workflow nodes */}
              {[
                { label: "Strategy", color: "bg-green/20 text-green", status: "✓" },
                { label: "Creative", color: "bg-orange/20 text-orange", status: "✓" },
                { label: "Policy", color: "bg-yellow/20 text-yellow", status: "!" },
              ].map((node) => (
                <div key={node.label} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`inline-grid h-5 w-5 place-items-center rounded text-[8px] font-bold ${node.color}`}>
                      {node.status}
                    </span>
                    <span className="text-[7px] uppercase tracking-wider text-white/20 font-bold">AI Assist</span>
                  </div>
                  <div className="text-[10px] font-bold text-white/70">{node.label}</div>
                  <div className="mt-1 h-1 w-full rounded-full bg-white/[0.06]">
                    <div className={`h-full rounded-full ${node.label === "Policy" ? "w-3/4 bg-yellow/40" : "w-full bg-green/40"}`} />
                  </div>
                </div>
              ))}
            </div>

            {/* Mock metrics row */}
            <div className="mx-4 mb-3 flex gap-3">
              {[
                { label: "Persona fit", value: "92", color: "text-green" },
                { label: "Policy score", value: "96", color: "text-green" },
                { label: "Channel fit", value: "88", color: "text-orange" },
              ].map((metric) => (
                <div key={metric.label} className="flex-1 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                  <div className={`font-display text-lg font-extrabold ${metric.color}`}>{metric.value}</div>
                  <div className="text-[8px] text-white/30 uppercase tracking-wider font-semibold">{metric.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Ambient glow behind the card */}
          <div className="absolute -bottom-10 left-1/2 -z-10 h-[200px] w-[80%] -translate-x-1/2 rounded-full bg-orange/[0.06] blur-[80px]" />
        </div>
      </div>

      {/* Subtle bottom edge line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-white/[0.06]" />
    </section>
  );
}
