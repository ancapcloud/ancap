import { describe, expect, it } from "vitest";
import { solutionPortfolio } from "../solutionPortfolio";
import { isTestProjectRoute, testProjectIds, testProjects } from "../testProjects";
import { testProjectsByLang } from "@/locales/testProjects";

describe("AI-created test projects", () => {
  it("keeps all five examples linked to their existing portfolio pages", () => {
    const portfolio = solutionPortfolio.flatMap(area => area.routes.map(([href, title]) => ({ href, title })));
    expect(testProjects).toHaveLength(5);
    expect(new Set(testProjects.map(project => project.href)).size).toBe(5);
    for (const project of testProjects) {
      expect(portfolio).toContainEqual({ href: project.href, title: project.title });
      expect(isTestProjectRoute(project.href)).toBe(true);
      expect(project.economySlug).toMatch(/^[a-z0-9-]+$/);
    }
    expect(isTestProjectRoute("/markets")).toBe(false);
    expect(isTestProjectRoute("/projects")).toBe(false);
  });

  it("provides explicit example disclosure and every project field in all five languages", () => {
    for (const lang of ["en", "ru", "uk", "de", "zh-Hant"] as const) {
      const copy = testProjectsByLang[lang];
      expect(Object.keys(copy).sort()).toEqual(Object.keys(testProjectsByLang.en).sort());
      expect(Object.keys(copy.projects).sort()).toEqual([...testProjectIds].sort());
      for (const [key, value] of Object.entries(copy)) {
        if (typeof value !== "string") continue;
        expect(value.trim(), `${lang}.${key}`).not.toBe("");
        if (lang !== "en") expect(value, `${lang}.${key}`).not.toBe(testProjectsByLang.en[key as keyof typeof copy]);
      }
      for (const id of testProjectIds) {
        expect(Object.keys(copy.projects[id]).sort()).toEqual(["ai", "deliverable", "goal", "people", "sample"]);
        for (const [field, value] of Object.entries(copy.projects[id])) {
          expect(value.trim(), `${lang}.${id}.${field}`).not.toBe("");
          if (lang !== "en") expect(value).not.toBe(testProjectsByLang.en.projects[id][field as keyof typeof copy.projects[typeof id]]);
        }
      }
    }
  });
});
