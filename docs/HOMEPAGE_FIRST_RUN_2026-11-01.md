# Homepage first-run redesign — 1 November 2026

Local implementation only. No production deployment or commercial activation claim.

## Experience

1. Wide split hero: product explanation, direct workflow CTA, catalogue link and semantic HTML workflow canvas with connected input/quote nodes, ANCAP execution node, report structure and receipt.
2. Redesigned CreatorAiConnect immediately below the hero: tool-specific paths and a copyable prompt panel, followed immediately by the redesigned Ask ANCAP assistant.
3. Compact execution / quote / result-and-receipt principles.
4. Recommended Token Risk Report with its inputs, output and one connected execution path.
5. Three discovery cards: token research, exchange listing preparation and growth campaign.
6. SolutionAreas, Smart Pay, WebInstallGuide, PeopleAiEconomySection, CardInfoSection,
   creator earnings, ReviewTrustSection, RacpOverview, investors and WorkflowFooter.

The homepage uses a 1600px canvas with responsive side padding; desktop typography and product artwork scale into the available width. Tablet/mobile stack the copy and canvas, and mobile simplifies the graph into a vertical progression.

The recommended route is `/ai/run/token-risk-report`. Unlike the Pro offer, this
existing workflow has a guided form rather than requiring JSON input. Its catalogue
and backend define a risk snapshot, trust signals, operational flags and receipt.
The homepage describes those output sections without inventing a report, price,
welcome-credit coverage or observed execution. Current price and availability
remain on the existing offer/run screens. Provider configuration and funding are
required for a real run; a generated shell is not independently verified research.

Marketing copy uses `useLanguage()` and a typed locale map, matching Projects /
`positioningByLang`. EN, RU, UK, DE and Traditional Chinese are supported. User-facing
copy explains actions and deliverables; experiment definitions stay in this document.
The later user-requested shared-system pass also revises navigation/footer styling; pricing/payment behavior and dependencies remain unchanged. See `FRONTEND_DESIGN_SYSTEM_2026-11-01.md`.

## Authentication

Guest run action carries `next=/ai/run/token-risk-report` to login. Switching to
registration preserves it, and successful email authentication returns to the
offer, including after the existing wallet-backup acknowledgement. Return targets
must be local paths; protocol-relative URLs and backslashes are rejected. Direct
auth visits still default to `/dashboard`. Wallet authentication behavior is retained.
Unsaved form inputs are not persisted across authentication.

## Measurement

Reuses `src/lib/analytics.ts` and its existing `ancap:analytics` browser event.
Both primary CTAs emit `homepage_primary_cta_click` with workflow slug, placement
(`hero` / `recommended`) and language. This helper emits an in-memory event; it is
not a durable collector or a measured conversion dashboard. No new storage,
third-party tracking or analytics platform was introduced.

Proposed supporting instrumentation for a separately scoped measurement task:

| Event | Source of truth |
| --- | --- |
| recommended workflow visit | Offer page reached, slug and homepage attribution |
| registration completed | Server-confirmed creation of a new account |
| workflow run started | Server-confirmed transition to `running` |
| workflow run completed | Server-confirmed transition to `completed` with a result |

Primary activation rate: distinct new registered users with at least one successful
completed workflow / all new registered users in the same cohort. Define an
observation window before comparing releases (proposed: seven days after account
creation). Deduplicate by user and run; exclude operator/test fixtures. Clicks,
visits, quoted runs and attempted runs are not completions. Keep degraded/stub
results separate from successful real execution. The backend status/result is
authoritative; browser receipt events alone must not establish success.

## Verification

Verified locally: 122 Vitest tests (23 files), 24 targeted Playwright scenarios,
TypeScript (`npx tsc --noEmit`), lint (`npm run lint`) and production build
(`npm run build`) all passed. The build generated 200 static pages and completed
route optimization/tracing. Browser widths: 1920, 1440, 768 and 390px. Both dark
and light themes were checked on representative public/catalogue/auth routes.
The existing Next lint deprecation and workspace-root notices remain.
Playwright coverage includes desktop/tablet/mobile layouts, five-language copy,
focus visibility, CTA destinations, existing AI onboarding and auth hand-off.
API responses in those browser checks are fixtures, not live paid runs.

## Review text

Suggested commit: `feat(frontend): refine marketing design system and first-run journey`

Suggested PR title: Refine ANCAP marketing design system and first-run journey

Suggested PR description:

Rebuild the homepage around a guided Token Risk Report and an HTML execution
canvas, with redesigned AI connection and assistant panels directly beneath the
hero. Expand the shared dark/light design system across public cards, typography,
buttons, forms, navigation, branding and the footer. Preserve workflow intent
through login/registration and reuse existing primary-CTA analytics. Add a site-wide Messenger-style Ask ANCAP dock with a shared
in-memory conversation, lazy panel loading and minimize/reopen behavior.

All five languages follow the existing locale-map architecture. Wallet/payment
behavior and workflow prices remain unchanged. Validation: 122 unit tests,
24 targeted browser scenarios, TypeScript, lint and production build passed.
Real paid completion, durable activation analytics and production deployment
remain separate acceptance gates.

A global Messenger-style Ask ANCAP dock also shares the inline conversation
across client-side routes. It loads its panel on demand and keeps draft/history
in memory while minimized. Full refresh clears the conversation.

## Changed-file inventory

```text
frontend-app/e2e/chat-dock.spec.ts
frontend-app/src/components/ClientProviders.tsx
frontend-app/src/components/AncapChatDock.module.css
frontend-app/src/components/AncapChatDock.tsx
frontend-app/src/components/AncapChatProvider.tsx
frontend-app/e2e/api-connection.spec.ts
frontend-app/e2e/design-system.spec.ts
frontend-app/e2e/home-assistant.spec.ts
frontend-app/e2e/home-first-run.spec.ts
frontend-app/e2e/investor-presentation.spec.ts
frontend-app/src/app/HomePage.tsx
frontend-app/src/app/ai/run/[template]/WorkflowTemplateView.tsx
frontend-app/src/app/ai/run/[template]/page.tsx
frontend-app/src/app/ai/workflows/WorkflowsCatalog.tsx
frontend-app/src/app/globals.css
frontend-app/src/app/icon.svg
frontend-app/src/app/layout.tsx
frontend-app/src/app/login/LoginForm.tsx
frontend-app/src/app/page.tsx
frontend-app/src/app/register/page.tsx
frontend-app/src/components/CreatorAiConnect.module.css
frontend-app/src/components/CreatorAiConnect.tsx
frontend-app/src/components/HomeChatDialog.module.css
frontend-app/src/components/HomeChatDialog.tsx
frontend-app/src/components/HomeFirstRun.module.css
frontend-app/src/components/HomeFirstRun.tsx
frontend-app/src/components/Navigation.tsx
frontend-app/src/components/NetworkBackground.tsx
frontend-app/src/components/ThemeProvider.tsx
frontend-app/src/components/WorkflowPresentation.module.css
frontend-app/src/components/WorkflowPresentation.tsx
frontend-app/src/components/workflow/WorkflowRunPanel.tsx
frontend-app/src/lib/__tests__/authReturn.test.ts
frontend-app/src/lib/authReturn.ts
frontend-app/src/locales/creatorAiConnect.ts
frontend-app/src/locales/homeChat.ts
frontend-app/src/locales/homeFirstRun.ts
MASTER_ROADMAP.md
PRODUCTION_ROADMAP.md
docs/HOMEPAGE_FIRST_RUN_2026-11-01.md
docs/FRONTEND_DESIGN_SYSTEM_2026-11-01.md
```
