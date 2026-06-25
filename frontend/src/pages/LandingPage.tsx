import { LandingNav } from "../components/landing/LandingNav";
import { HeroSection } from "../components/landing/HeroSection";
import { StatsMarquee } from "../components/landing/StatsMarquee";
import { FeaturesBento } from "../components/landing/FeaturesBento";
import { WorkflowSection } from "../components/landing/WorkflowSection";
import { CTASection } from "../components/landing/CTASection";
import { Footer } from "../components/landing/Footer";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-surface font-sans">
      <LandingNav />
      <HeroSection />
      <StatsMarquee />
      <FeaturesBento />
      <WorkflowSection />
      <CTASection />
      <Footer />
    </div>
  );
}
