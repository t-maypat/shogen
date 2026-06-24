import { Github, Twitter, Linkedin } from "lucide-react";

const footerLinks = {
  Product: ["Features", "Workflow", "Pricing", "Changelog"],
  Resources: ["Documentation", "API Reference", "Blog", "Case Studies"],
  Company: ["About", "Careers", "Contact", "Privacy"],
};

export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] bg-[#121514]">
      <div className="mx-auto max-w-7xl px-6 py-16 lg:px-8">
        <div className="grid gap-12 md:grid-cols-5">
          {/* Brand column */}
          <div className="md:col-span-2">
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
              </div>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/35">
              AI-powered campaign intelligence platform. From brief to optimized
              deployment in one collaborative workspace.
            </p>
            <div className="mt-6 flex gap-3">
              {[
                { Icon: Twitter, label: "Twitter" },
                { Icon: Github, label: "GitHub" },
                { Icon: Linkedin, label: "LinkedIn" },
              ].map(({ Icon, label }) => (
                <a
                  key={label}
                  href="#"
                  aria-label={label}
                  className="grid h-9 w-9 place-items-center rounded-lg border border-white/[0.08] text-white/30 transition-all hover:border-white/15 hover:text-white/60"
                >
                  <Icon size={15} />
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="mb-4 text-xs font-bold uppercase tracking-[0.1em] text-white/50">
                {category}
              </h3>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-sm text-white/30 transition-colors hover:text-white/60"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-white/[0.06] pt-8 sm:flex-row">
          <span className="text-xs text-white/20">
            © {new Date().getFullYear()} Shogun. All rights reserved.
          </span>
          <div className="flex gap-6 text-xs text-white/20">
            <a href="#" className="transition-colors hover:text-white/40">
              Terms
            </a>
            <a href="#" className="transition-colors hover:text-white/40">
              Privacy
            </a>
            <a href="#" className="transition-colors hover:text-white/40">
              Cookies
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
