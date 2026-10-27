import { describe, expect, it } from "vitest";
import prices from "./catalogPrices.json";
import backendPrices from "../../../app/services/catalog_prices.json";
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
  it("keeps backend and frontend prices aligned, including server-only subscriptions", () => {
    expect(prices).toEqual(backendPrices);
    for (const [period, amount] of Object.entries({ monthly: "29", quarterly: "79", annual: "290" })) {
      expect(prices[`stardust-weather-control-subscription:${period}` as keyof typeof prices]).toBe(amount);
    }
  });
  it.each([
    ["aeterna-m-receptor-subscription", ["19", "49", "190"]],
    ["aeterna-pulmopure-subscription", ["19", "49", "190"]],
  ])("uses USD prices for every billing period of %s", (slug, amounts) => {
    const template = fallbackWorkflowTemplates.find(item => item.slug === slug)!;
    expect(template).toBeDefined();
    for (const [index, period] of (["monthly", "quarterly", "annual"] as const).entries()) {
      expect(template[`subscription_price_${period}`]).toEqual({ amount: amounts[index], currency: "USD" });
    }
  });
});
