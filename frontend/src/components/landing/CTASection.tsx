import { useNavigate } from "react-router-dom";
import { ArrowRight, Zap } from "lucide-react";

export function CTASection() {
  const navigate = useNavigate();

  return (
    <section
      id="pricing"
      className="relative overflow-hidden bg-header py-28 sm:py-36"
    >
      {/* Background effects */}
      <div className="absolute inset-0">
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "radial-gradient(rgba(255,255,255,0.8) 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="absolute -left-40 top-[-150px] h-[500px] w-[500px] animate-orbit rounded-full border border-orange/[0.06]" />
        <div className="absolute -right-20 bottom-[-100px] h-[400px] w-[400px] animate-orbit-reverse rounded-full border border-green/[0.05]" />
        <div className="absolute left-1/2 top-1/2 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-orange/[0.03] blur-[150px]" />
      </div>

      {/* Content */}
      <div className="relative z-10 mx-auto max-w-3xl px-6 text-center lg:px-8">
        {/* Icon */}
        <div className="mx-auto mb-8 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.05] border border-white/[0.08]">
          <Zap size={24} className="text-orange" />
        </div>

        <h2 className="font-display text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
          Ready to orchestrate{" "}
          <span className="bg-gradient-to-r from-orange via-yellow to-orange bg-clip-text text-transparent">
            smarter campaigns?
          </span>
        </h2>

        <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-white/45">
          Get from brief to optimized deployment in minutes, not weeks. Start
          your first AI-powered campaign workflow today.
        </p>

        {/* CTA buttons */}
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <button
            onClick={() => navigate("/app")}
            className="group flex items-center gap-2 rounded-xl bg-orange px-8 py-4 text-base font-bold text-white animate-glow-pulse transition-all hover:-translate-y-0.5"
          >
            Start free workspace
            <ArrowRight
              size={18}
              className="transition-transform group-hover:translate-x-1"
            />
          </button>
        </div>

        {/* Trust row */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs text-white/30">
          <span className="flex items-center gap-1.5">
            <span className="h-1 w-1 rounded-full bg-green" />
            No credit card required
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1 w-1 rounded-full bg-green" />
            Free tier available
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1 w-1 rounded-full bg-green" />
            SOC 2 compliant
          </span>
        </div>
      </div>
    </section>
  );
}
