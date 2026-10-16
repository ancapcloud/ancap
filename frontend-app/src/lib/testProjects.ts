import { solutionPortfolio } from "./solutionPortfolio";

/** Curated AI-authored examples, separate from live orders and executable offers. */
export const testProjectIds = ["aeterna", "galaxy", "lunar", "stardust", "starlink"] as const;
export type TestProjectId = typeof testProjectIds[number];

/** Economy catalog slugs for the first five platform seed projects. */
export const economySeedSlugs: Record<TestProjectId, string> = {
  aeterna: "aeterna-longevity-brief",
  galaxy: "galaxy-edge-infra-concept",
  lunar: "lunar-catalog-card",
  stardust: "stardust-weather-brief",
  starlink: "starlink-install-intake",
};

const portfolioRoutes = solutionPortfolio.flatMap(area =>
  area.routes.map(([href, title]) => ({ href, title })),
);

/** The portfolio remains the source of truth for project names and destination routes. */
export const testProjects = testProjectIds.map(id => {
  const route = portfolioRoutes.find(item => item.title.toLowerCase() === id);
  if (!route) throw new Error(`Missing portfolio route for test project: ${id}`);
  return { id, ...route, economySlug: economySeedSlugs[id] };
});

export function isTestProjectRoute(pathname: string): boolean {
  return testProjects.some(project => project.href === pathname);
}
