import { Scale, Wallet, Settings, Target, Package, Search, LucideIcon } from "lucide-react";

/** lucide-react icon per review domain, replacing the old emoji map
 * (design handoff explicitly calls for lucide-react over emoji/inline SVG). */
export const DOMAIN_LUCIDE_ICONS: Record<string, LucideIcon> = {
  legal: Scale,
  financial: Wallet,
  technical: Settings,
  risk: Target,
  delivery: Package,
};

export function getDomainIcon(domain: string): LucideIcon {
  return DOMAIN_LUCIDE_ICONS[domain] || Search;
}
