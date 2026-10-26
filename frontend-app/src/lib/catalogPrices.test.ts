import { describe, expect, it } from "vitest";
import { catalogPriceLabel, fallbackWorkflowBundles, fallbackWorkflowTemplates } from "./workflowStore";

describe("retail catalogue", () => {
  it("shows USD faces without fabricating an offline token quote", () => {
    const perfume = fallbackWorkflowTemplates.find(item => item.slug === "aeterna-dna-pheromone-perfume")!;
    expect(catalogPriceLabel(perfume)).toBe("$29");
    expect(perfume.price.currency).toBe("USD");
    expect(perfume.price_acp).toBeUndefined();
    expect(perfume.description).toContain("brief and intake preparation only");
  });
  it("uses USD instead of large token quotes for browsing", () => {
    expect(catalogPriceLabel({price: {amount: "1950000.00", currency: "ACP"}, usd_sticker: {amount: "39.00", currency: "USD"}})).toBe("$39");
  });
  it("calculates bundle discounts from included products", () => {
    for (const bundle of fallbackWorkflowBundles) {
      const total = bundle.workflow_slugs.reduce((sum, slug) => sum + Number(fallbackWorkflowTemplates.find(item => item.slug === slug)!.price.amount), 0);
      expect(Number(bundle.price.amount)).toBeLessThan(total);
      expect(bundle.discount_percent).toBe(Math.floor((1 - Number(bundle.price.amount) / total) * 100));
    }
  });
  it("uses correct subscription keys with hyphens", () => {
    const monthly = fallbackWorkflowTemplates.find(item => item.slug === "aeterna-m-receptor-subscription-monthly")!;
    expect(monthly).toBeDefined();
    expect(monthly.price.amount).toBe("19");
  });
});
