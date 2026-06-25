export function StatsMarquee() {
  const stats = [
    { text: "3 AI Personas", icon: "👤" },
    { text: "9 Channel Variants", icon: "📢" },
    { text: "10-Stage Pipeline", icon: "⚡" },
    { text: "Policy-Safe Creative", icon: "🛡️" },
    { text: "Synthetic Evaluation", icon: "📊" },
    { text: "Wave 2 Optimization", icon: "🔄" },
    { text: "Multi-Channel Orchestration", icon: "🎯" },
    { text: "Real-time Scoring", icon: "✨" },
  ];

  const Row = ({ reverse = false }: { reverse?: boolean }) => (
    <div className="marquee-mask overflow-hidden">
      <div className={`flex gap-4 ${reverse ? "animate-marquee-reverse" : "animate-marquee"}`}>
        {/* Duplicate for seamless loop */}
        {[...stats, ...stats].map((stat, i) => (
          <div
            key={i}
            className="flex shrink-0 items-center gap-2.5 rounded-full border border-line bg-paper px-5 py-2.5 shadow-[0_1px_3px_rgba(24,28,26,0.04)]"
          >
            <span className="text-sm">{stat.icon}</span>
            <span className="whitespace-nowrap text-sm font-semibold text-ink/80">
              {stat.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <section className="overflow-hidden bg-surface py-16">
      <div className="space-y-4">
        <Row />
        <Row reverse />
      </div>
    </section>
  );
}
