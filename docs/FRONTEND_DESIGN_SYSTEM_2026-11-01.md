# ANCAP frontend design system and marketing review

1 November 2026. Local implementation; no production deployment.

## Implemented visual system

The visual direction is a dark navy application surface with mint/cyan emphasis,
secondary violet detail, a geometric ANCAP mark, restrained borders and clear
typographic hierarchy. Meaningful product content remains semantic HTML. The
homepage workflow canvas describes real output sections without inventing scores,
customers, prices, live executions or partnerships.

Shared coverage:

- `frontend-app/src/app/globals.css`: dark/light tokens, surfaces, buttons, cards,
  text controls, native checkbox/radio sizing, badges, tables, focus and reduced motion.
- `frontend-app/src/components/ThemeProvider.tsx`: selects theme classes; CSS owns
  the token values instead of duplicating them in JavaScript.
- `frontend-app/src/components/Navigation.tsx`: geometric mark and wider layout,
  preserving routes, authentication, menu, language and wallet behavior.
- `frontend-app/src/components/WorkflowPresentation.module.css`: shared public-page
  typography, layout, actions, cards, tags, notes, links and footer.
- `frontend-app/src/components/WorkflowPresentation.tsx`: application-area line icons
  and a structured brand/navigation footer.
- `frontend-app/src/app/icon.svg`: matching vector favicon.
- Workflow catalogue and offer layouts use a wider 1440px canvas. The homepage uses
  1600px with responsive side padding.

The presentation styles also improve SolutionAreas, PeopleAiEconomySection,
CardInfoSection, ReviewTrustSection, WebInstallGuide, Projects, and investor pages
where those components reuse the shared primitives. Legacy route-specific inline
styles and every authenticated screen have not all been individually redesigned.

## Homepage composition

Hero with an HTML workflow canvas → redesigned AI connection panel → redesigned
Ask ANCAP → product principles → recommended Token Risk Report → three discovery
cards → application areas → Smart Pay → install guide → People + AI → card concept
→ creators → review evidence → rACP → investors → shared footer.

The AI panel and assistant sit directly below the hero at the user's request.
The assistant has a visible heading, a proper composer, suggested actions and
explicit offline fallback navigation. Its configured state retains real messaging,
free-model pinning, voice input and fullscreen. Fullscreen traps keyboard focus,
supports Escape and restores focus to its opener. This does not change backend
model selection, credentials, billing, wallet or payment behavior.

Marketing strings use language-keyed locale files: `homeFirstRun.ts`,
`creatorAiConnect.ts` and `homeChat.ts`. Existing shared positioning translations
remain the source for ecosystem copy. The copy-confirmation state resets when
the selected language changes.

## Token ownership

| Token group | Purpose |
| --- | --- |
| `--bg`, `--bg-elev-1`, `--bg-card` | Page and layered application surfaces |
| `--surface-gradient`, `--surface-wash` | Cards and quiet secondary treatments |
| `--text`, `--text-muted` | Primary and supporting content |
| `--accent`, `--accent-strong`, `--accent-dim` | Action and focus hierarchy |
| `--accent-secondary` | Secondary category detail |
| `--border`, `--border-strong` | Resting and emphasized boundaries |
| `--radius-md`, `--radius-lg`, `--shadow-soft` | Consistent shape and depth |

Use shared primitives before adding another local button/card style. Keep local
illustration styling scoped to a CSS module. Reserve bright accents for meaningful
actions; keep body copy readable and avoid decorative animation on marketing pages.

## Prioritized frontend marketing improvements

These are product hypotheses to test, not claimed conversion gains.

1. **Tighten catalogue decisions.** `WorkflowsCatalog.tsx` presents Studio,
   dashboard, pricing, sample-report and seller actions near its introduction.
   Lead with the visitor's task and a small set of suitable offers; give each
   offer one clear next action. Keep advanced buyer/developer/creator paths
   discoverable after the initial choice.
2. **Demonstrate the actual result.** Add a reviewed, clearly labelled sample and
   a short recorded real run for the recommended workflow. Connect input, quote,
   output and receipt in one story. State source gaps and degraded/stub results
   explicitly. A decorative risk score must never stand in for a verified report.
3. **Measure successful activation.** The browser event helper is not a durable
   analytics pipeline. Attribute registration and completed runs server-side,
   deduplicate users/runs and compare a fixed cohort window. Exclude fixtures,
   operator runs and degraded outputs. See the companion homepage experiment note.
4. **Create focused audience entry pages.** Crypto research buyers, launch teams,
   workflow creators and API integrators need different examples and CTAs. Reuse
   the design system and real catalogue entries rather than expanding the hero.
5. **Turn proof into trust.** Link a real receipt and a sample deliverable next to
   the offer. Add customer case studies only with verified outcomes and permission.
   Keep release/test evidence separate from customer traction and revenue.
6. **Finish search/share presentation.** The audited root metadata has no custom
   Open Graph image. Build a branded share card, inspect canonicals/sitemaps and
   give indexable language variants appropriate localized metadata and hreflang.
   Add structured data only for facts and offers actually shown on the page.
   [Google's software application guidance](https://developers.google.com/search/docs/appearance/structured-data/software-app)
   explains supported fields; its
   [structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)
   require accurate, representative content. Rich-result appearance is not guaranteed.
7. **Reduce and measure the client payload.** The successful local production build
   reports 643 kB first-load JavaScript for the homepage. That is a bundle-size
   observation, not a measured Core Web Vitals result or a before/after saving.
   Profile chunk ownership, shared client providers and locale payloads before
   choosing code-splitting boundaries; load advanced capabilities on intent where
   appropriate. Record LCP, INP and CLS on real
   mobile visits and check the first-run path as well as the home route. Defer
   heavy secondary experiences where measurements justify it. The marketing
   homepage now avoids the existing animated network canvas.
   [Google's Core Web Vitals guidance](https://developers.google.com/search/docs/appearance/core-web-vitals)
   and [web.dev's measurement guidance](https://web.dev/articles/vitals) distinguish
   real-user evaluation from a single lab run.
8. **Verify catalogue-grounded recommendations.** At the start of this audit the
   homepage assistant used a descriptive system prompt. Separately authored backend
   edits now present in the shared checkout add bounded read-only catalogue/guide
   lookups. They are outside this frontend contribution and were not verified here.
   Validate recommendations against currently published offers before promoting
   this capability, and retain explicit user review before paid actions. Offline
   browsing must continue to work; chat should not become a prerequisite for value.

## Where the AI lives

The repository contains several different AI-related layers:

| Purpose | Files |
| --- | --- |
| Homepage assistant UI and shared client runtime | `frontend-app/src/components/HomeChatDialog.tsx`, `AncapChatProvider.tsx`, their styles/locales |
| Site-wide Messenger-style dock | `frontend-app/src/components/AncapChatDock.tsx`, its CSS module and `ClientProviders.tsx` |
| Assistant prompts, free-model selection and inference | `app/services/home_chat.py` (`build_messages`, `complete_home_chat`) |
| Public chat endpoints and request schemas | `app/api/routers/home_chat.py`, `app/schemas/home_chat.py` |
| Paid workflow inference, retry/fallback and usage recording | `app/services/llm.py` (`execute_paid_workflow_with_llm`) |
| Workflow templates and output construction | `app/services/workflow_execution.py` |
| Workflow API, execution and operations | `app/api/routers/workflow_store.py`, `app/services/workflow_ops.py` |
| Registered agent identities and API schemas | `app/api/routers/agents.py`, `app/schemas/agents.py`, `Agent` in `app/db/models.py` |
| External AI-agent access over remote MCP | `app/api/routers/mcp.py`, `app/services/mcp_remote.py` |
| Local stdio MCP adapter | `mcp-server/ancap_mcp_server.py` |

The homepage assistant uses OpenRouter on the server. Its system prompt explicitly
states that it cannot access wallets, sign transactions, move ACP or start jobs.
It is a conversational guide, separate from paid execution. Separately authored
working-tree changes add read-only lookup helpers; those backend edits are not
part of, or verified by, this frontend contribution. The paid LLM layer
supports configured providers and records fallback/failure information. Agent
registration records identities; it does not by itself create an autonomous worker.

The tracked Theodore files include operator promotion helpers
(`scripts/theodore-earn-promo.ps1`, `scripts/theodore-earn-skus.json`); those are not
the full standalone Theodore/OpenClaw runtime. `AGENTS.md` provides coding-agent
instructions and is not the website's AI inference implementation.

## Review and verification

No production deployment, external publication or real paid run was performed.
122 unit tests, 24 targeted Playwright scenarios, TypeScript, lint and the
production build passed. The build generated 200 static pages successfully.
See `HOMEPAGE_FIRST_RUN_2026-11-01.md` for the complete changed-file inventory and
review text. Browser checks use explicit local fixtures for chat, accounts and keys.
The audit covers representative public/catalogue/auth routes in both themes,
responsive widths, all five homepage locales, assistant online/offline behavior,
clipboard confirmation, authentication return intent and keyboard fullscreen.


## Site-wide Ask ANCAP dock

Inspired by the launcher/window interaction and shared conversation pattern in
Blink2's `StarliChatDock` / `blinkChatStore`, the ANCAP implementation uses its own
existing chat endpoint and design system. It does not import Blink's client,
backend, accounts or messaging service.

`AncapChatProvider` owns one in-memory draft, transcript, selected free model,
request state and availability result. The homepage's inline chat and the global
dock consume that same state. Minimizing/closing a window and client-side route
navigation preserve the conversation; a full refresh clears it. Message text is
not automatically copied into browser storage. New chat aborts the pending request
and prevents a late response from entering a new conversation.

The dock provides a responsive bottom-right launcher, compact window, minimize,
close, fullscreen, Escape and focus return. It is mounted through ClientProviders
on all routes. The panel loads dynamically; non-home routes do not request chat
availability before opening it. Its launcher avoids the existing Stardust support
control. No fake online state or unread counters are displayed.

Additional browser coverage verifies lazy availability, minimizing/reopening with
a retained draft, shared inline/dock messages, route navigation, reset, mobile fit
and fullscreen. These three new scenarios and the three existing assistant
scenarios pass; total scoped browser coverage is 24 distinct scenarios.
