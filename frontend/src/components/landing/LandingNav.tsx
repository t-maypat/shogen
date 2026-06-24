import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react";

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const navLinks = [
    { label: "Features", href: "#features" },
    { label: "Workflow", href: "#workflow" },
    { label: "Pricing", href: "#pricing" },
  ];

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-header/90 backdrop-blur-xl shadow-[0_1px_0_rgba(255,255,255,0.06)]"
          : "bg-transparent"
      }`}
      style={{ color: "white" }}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="relative grid h-8 w-8 rotate-45 place-items-center rounded-lg bg-orange shadow-[inset_0_0_0_1px_rgba(255,255,255,0.18)]">
            <span className="z-1 -rotate-45 font-display text-sm font-extrabold text-white">
              S
            </span>
            <div className="absolute inset-[5px] rounded-[4px] border border-white/40" />
          </div>
          <div>
            <div className="font-display text-sm font-extrabold tracking-[0.16em] text-white">
              SHOGUN
            </div>
            <div className="text-[8px] uppercase tracking-[0.09em] text-white/40">
              Campaign intelligence
            </div>
          </div>
        </div>

        {/* Desktop links */}
        <div className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-white/60 transition-colors hover:text-white"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* CTA */}
        <div className="hidden items-center gap-4 md:flex">
          <button
            onClick={() => navigate("/app")}
            className="text-sm font-semibold text-white transition-colors hover:text-orange"
          >
            Sign in
          </button>
          <button
            onClick={() => navigate("/app")}
            className="rounded-lg bg-orange px-5 py-2.5 text-sm font-bold text-white shadow-[0_0_20px_rgba(220,103,72,0.25)] transition-all hover:-translate-y-0.5 hover:shadow-[0_0_30px_rgba(220,103,72,0.4)]"
          >
            Get started
          </button>
        </div>

        {/* Mobile menu button */}
        <button
          className="text-white md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-white/10 bg-header/95 backdrop-blur-xl md:hidden">
          <div className="space-y-1 px-6 py-4">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="block rounded-lg px-3 py-2 text-sm font-medium text-white/70 transition-colors hover:bg-white/5 hover:text-white"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <div className="pt-3 border-t border-white/10 mt-3">
              <button
                onClick={() => navigate("/app")}
                className="w-full rounded-lg bg-orange px-5 py-2.5 text-sm font-bold text-white"
              >
                Get started
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
