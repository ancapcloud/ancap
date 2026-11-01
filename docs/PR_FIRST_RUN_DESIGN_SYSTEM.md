# Refine ANCAP marketing design and the path to a first successful workflow

## Summary

Rebuild the homepage around one guided Token Risk Report entry point and an HTML
input → quote → execution → result/receipt canvas. Add redesigned AI onboarding
and a site-wide Messenger-style Ask ANCAP dock sharing its conversation with the
inline homepage assistant. Preserve workflow intent through login/registration.

Improve shared dark/light tokens, navigation, branding, typography, cards, buttons,
forms and footer, with responsive layouts and five-language marketing copy.
Custom wallet, dashboard and Studio screens are not individually redesigned.

The backend concierge supports one validated read-only catalogue/guide lookup,
bounded model fallbacks and a total request deadline. It preserves the free-only
model policy and does not gain wallet, payment or job-execution permissions.

No new UI/analytics framework, workflow price changes or production deployment.
Work is bounded to the requested four-hour task; further custom-screen redesign,
live-provider evaluation and durable analytics are follow-up work.

## Relevant checks

- Backend: 20 tests passed in `tests/api/test_home_chat.py` and
  `tests/unit/test_text_security_regressions.py`, using Python 3.11 with the pinned
  runtime inputs. Reverified before preparing this combined PR.
- Frontend: 122 Vitest tests passed across 23 files.
- Browser: 24 targeted Playwright scenarios passed across the scoped runs,
  covering responsive widths, both themes, five-language homepage copy,
  authentication return paths, API-key onboarding, clipboard behavior, shared
  chat state, minimize/reopen, route navigation, offline fallback and fullscreen.
- TypeScript: `npx tsc --noEmit` passed.
- Lint: `npm run lint` passed.
- Production build: `npm run build` passed, including 200 static pages.

The browser tests use explicit account/chat fixtures. They do not establish a
successful live paid run or live-model response quality. Existing dependency
deprecation notices remain; they did not fail these checks.

## How to measure the result

Primary metric: distinct newly registered users who complete at least one
successful workflow within seven days / all newly registered users in that cohort.
Use the server-confirmed `completed` state with a real result; exclude test/operator
runs and distinguish degraded/stub outputs. Clicks, quotes and attempted runs do
not count as activation.

Supporting funnel: homepage primary CTA click → recommended offer visit →
registration completed → workflow started → workflow completed. The homepage
CTAs reuse the existing `ancap:analytics` browser helper with slug, placement and
language. Durable collection, registration attribution and completion/cohort
reporting remain proposed work, not an implemented analytics platform.

After deployment approval, compare equivalent seven-day registration cohorts
against the prior homepage, controlling for acquisition channel and excluding
unfinished observation windows. No conversion uplift is claimed by this PR.

## Review and deployment

Production deployment is intentionally left for the owner's review. This PR
should remain unmerged until that review is complete. Local frontend preview,
automated fixtures and a production build are separate from live acceptance.

Detailed inventory and limitations:

- [Homepage implementation](HOMEPAGE_FIRST_RUN_2026-11-01.md)
- [Design system, marketing priorities and AI file map](FRONTEND_DESIGN_SYSTEM_2026-11-01.md)
- [Backend concierge scope](HOME_CHAT_CONCIERGE.md)
