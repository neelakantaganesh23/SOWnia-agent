# Handoff: SOWnia Vivid UI (gradient / glassmorphism)

## Overview
SOWnia is an AI-powered multi-agent tool that reviews Statement of Work (SOW) documents. Five specialist agents (Legal, Financial, Technical, Risk, Delivery) examine an uploaded SOW in parallel and produce structured, page-cited findings with an overall risk score. This handoff documents the **"Vivid" visual direction** — a dark, animated, glassmorphic UI — across four screens: **Login → Upload/Landing → Review Results → Dashboard**.

The target is the existing **Next.js + Tailwind** frontend in `neelakantaganesh23/SOWnia-agent` (`frontend/`).

## About the Design Files
The file in this bundle (`SOWnia Vivid.dc.html`) is a **design reference created in HTML** — a prototype showing the intended look, animation, and behavior. It is **not production code to copy directly**. It uses a small custom template runtime (`<x-dc>`, `<sc-if>`, `<sc-for>`, `{{ }}` holes) that does not exist in your app.

Your task: **recreate this design in the existing Next.js + Tailwind codebase**, reusing its established patterns — the App Router pages, the Zustand `reviewStore`, the `/api/v1/*` calls in `lib/api.ts`, the `lib/types.ts` interfaces, and the existing component split (`AgentCard`, `FindingsList`, `RiskBadge`, `ConfidenceBar`, `ReviewHistoryTable`, `FileUploadZone`). Restyle those components to this Vivid look; do not rebuild the data layer.

## Fidelity
**High-fidelity (hifi).** Colors, typography, spacing, gradients, and animations below are final. Recreate the UI to match — port the exact tokens into `tailwind.config.ts` / `globals.css` and match the animations.

---

## Design Tokens

### Colors
| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#0a0a11` | Page background (near-black) |
| `--ink` | `#f4f5fb` | Primary text |
| `--mut` | `rgba(244,245,251,.62)` | Secondary text |
| `--mut2` | `rgba(244,245,251,.4)` | Tertiary / placeholder text |
| `--glass` | `rgba(255,255,255,.045)` | Glass surface fill |
| `--glassbrd` | `rgba(255,255,255,.11)` | Glass border |
| Signature gradient | `linear-gradient(120deg,#38BDF8 0%,#A855F7 34%,#EC4899 66%,#FB923C 100%)` | Brand mark, primary buttons, gradient text, accents |
| Risk HIGH | text `#FB4E6D` on `rgba(251,78,109,.16)` | High-risk badges/bars |
| Risk MEDIUM | text `#FBBF24` on `rgba(251,191,36,.16)` | Medium-risk badges/bars |
| Risk LOW | text `#34D399` on `rgba(52,211,153,.16)` | Low-risk badges/bars |
| Accent violet (labels/links) | `#C084FC` | Section kickers, links |
| Status: in progress | `#38BDF8` on `rgba(56,189,248,.16)` | Dashboard status pill |
| Status: error | `#FB4E6D` on `rgba(251,78,109,.16)` | Dashboard status pill |

> NOTE: risk hexes here are the Vivid palette. The backend/`types.ts` `RISK_COLORS` use `#ef4444 / #f59e0b / #22c55e`. Keep the backend enums; map them to these Vivid display colors in the UI layer.

### Typography
- **Headings / display / numbers:** `Plus Jakarta Sans`, weights 500–800, `letter-spacing: -0.02em`. Google Fonts.
- **Body / UI:** `Inter`, weights 400–600. Google Fonts.
- Heading sizes seen: hero `clamp(40px,5vw,64px)/800`; transition hero `clamp(38px,7vw,80px)/800`; page H1 `40px/800`; card title `18–19px/700`; stat number `38px/800`; body `14–17px`.

### Surface / effects
- **Glass card:** `background:var(--glass)`, `border:1px solid var(--glassbrd)`, `backdrop-filter:blur(18px)`.
- **Radius:** cards `18–26px`, buttons `11–14px`, inputs `12px`, pills `999px`. (Vivid uses generous rounding — this is intentional and unlike a flat system.)
- **Gradient button:** the signature gradient fill, `color:#0a0a11`, `font-weight:700`, shadow `0 8px 30px -6px rgba(168,85,247,.55)`; hover lifts `translateY(-2px)` with a pink-tinted shadow.
- **Secondary button (`gbtn2`):** `rgba(255,255,255,.05)` fill, `var(--glassbrd)` border; hover brightens fill + `translateY(-2px)`.
- **Input focus:** border `#A855F7` + `box-shadow:0 0 0 3px rgba(168,85,247,.22)`.
- **Lift-on-hover cards:** `translateY(-6px)`, brighter border, deep shadow `0 24px 60px -20px rgba(0,0,0,.7)`.
- **Animated mesh background (all screens):** four blurred color blobs (`#38BDF8`, `#A855F7`, `#EC4899`, `#FB923C`), `filter:blur(70px)`, `opacity ~.4–.55`, `position:fixed;inset:0`, each drifting via keyframes `meshA/B/C` (16–24s ease-in-out infinite).

### Key animations (durations / easing)
| Name | What | Spec |
| --- | --- | --- |
| `gradShift` | Gradient text/buttons shimmer | `background-position` 0↔100%, 8s ease infinite |
| `fadeUp` (`.fu`) | Content enter | opacity 0→1, translateY 26px→0, .7s cubic-bezier(.2,.7,.3,1) |
| `revLine` | Transition headline reveal | opacity+translateY(40px)+blur(8px)→0, .9s, staggered .25s/.7s |
| `chipPop` | Transition agent chips pop in | scale .7→1.06→1, .5s, staggered from 1.1s +0.28s each |
| `prog` | Transition progress bar | width 0→100%, 3.1s cubic-bezier(.5,0,.2,1) |
| `ringDraw` | Risk gauge ring | stroke-dashoffset 327→~105, 1.8–2.4s cubic-bezier(.4,0,.2,1) |
| `floatY` / `floatChip` | Mockup + floating chips bob | translateY, 5–7s ease-in-out infinite |
| `barLoop` / `fillBar` | Confidence bars | width 0→value |
| `growBar` | Dashboard distribution bars | scaleY 0→1, .9s |
| `pulseDot` | "API Connected" dot | opacity + expanding ring, 2.5s infinite |

The prototype also exposes **Motion** presets that should map to a reduced-motion strategy: `Lively` (default), `Calm` (slower durations), `Still` (animations off). At minimum, honor `prefers-reduced-motion` by disabling the mesh/float/pulse loops.

### Spacing
Page max-width `1180px`, side padding `24px`. Card padding `20–44px`. Grid gaps `16–48px`. Nav is a sticky glass bar `margin:16px auto 0`, padding `11px 18px`, radius `16px`.

---

## Screens / Views

### 1. Login  (`screenshots/01-login.png`)
- **Purpose:** Authenticate, then kick off the transition into the app.
- **Layout:** Full-viewport `display:grid; place-items:center`, over the mesh background. Single centered glass card, `max-width:440px`, radius `26px`, padding `44px 40px`.
- **Components (top→bottom):**
  - Brand lockup: 42px gradient rounded-square with "S", wordmark "SOWnia" (Plus Jakarta 800/22px).
  - H1 "Welcome back" (30px/800); subtitle "Sign in to run a multi-agent review in minutes." (`--mut`, 14.5px).
  - "Continue with Google" — full-width `gbtn2`, 46px, multicolor Google "G" SVG at left of centered label.
  - "OR" divider: two 1px rules flanking uppercase 11px `--mut2` label.
  - "Work email" label + email input (`in-field`, 46px, placeholder `you@company.com`).
  - "Password" row: label left, "Forgot?" link right (`#C084FC`); password input (placeholder `••••••••••`).
  - Primary gradient button "Sign in & review →" (48px).
  - Ghost button "Email me a magic link instead" (mail SVG + label, `--mut`).
  - Footer: "New here? **Request access**" (violet link).
- **Behavior:** All three auth actions (Google, Sign in, magic link, Request access) call the same `enter` handler → go to Transition.

### 2. Transition  (interstitial, ~3.4s — not a routed screen)
- **Purpose:** Branded loading beat after sign-in before the app.
- **Layout:** Full-viewport centered column over mesh.
- **Components:** Uppercase kicker "Setting up your workspace"; two-line hero — line 1 "Review SOW Documents" (gradient text), line 2 "in Minutes, Not Days" — revealed with `revLine` stagger; a row of 5 glass pill chips (one per agent, colored dot + name + check) popping in via `chipPop`; a 320px gradient progress bar (`prog`).
- **Behavior:** Auto-advances to Upload after ~3.4s (`setTimeout`). In the real app, gate this on the auth/session request resolving rather than a fixed timer, but keep the ~min-duration reveal so it doesn't flash.

### 3. Upload / Landing  (`screenshots/02-upload.png`)  →  `frontend/app/page.tsx`, `components/upload/FileUploadZone.tsx`
- **Purpose:** Landing + entry point to upload a SOW and start a review.
- **Layout:** Sticky glass nav at top. Two-column hero `grid-template-columns:1.05fr .95fr; gap:48px`. Below: 3-column feature grid, `margin-top:80px`.
- **Nav:** brand lockup (click → Upload) at left; links Upload / Review / Dashboard (active link gets a lit background via `aria-current="page"`); a 1px divider; "● API Connected" with pulsing green dot; "Sign out".
- **Hero left (copy):** glass pill badge "AI-Powered Multi-Agent Review"; H1 "Review SOW Documents / *in Minutes, Not Days*" (second line gradient text); paragraph describing the five agents; button row — primary "Upload & review" (up-arrow icon) + secondary "See how it works"; stat row "5 specialist agents · ~3 min per document · 100% page-cited" (gradient numbers).
- **Hero right (mockup):** a floating glass "Review results" card (`floatY`) previewing the review UI — HIGH·6.8 pill, a `ringDraw` gauge + skeleton summary lines, four agent confidence bars (`barLoop`); plus two absolutely-positioned floating chips ("3 agents done", "+ Annotated PDF"). This is decorative — in production it can be a static/animated illustration.
- **Feature cards (3):** icon tile (colored, `data-om-raster` in the mock — use a real Lucide icon in code), title, description. Titles: "Five specialist agents", "Structured findings", "A weighted verdict". Hover = lift.
- **Behavior:** "Upload & review" navigates to Review in the mock; in production it triggers the real upload flow (`FileUploadZone` → upload API → start review → route to `/review/[id]`).

### 4. Review Results  (`screenshots/03-review.png`)  →  `frontend/app/review/[id]/page.tsx` + review components
- **Purpose:** Show the completed multi-agent review of one document.
- **Layout:** Header row (title block left, export buttons right, wraps); overall-risk glass panel (`grid-template-columns:auto 1fr; gap:40px`); then a 2-column grid of agent cards.
- **Header:** violet kicker "Review complete"; H1 "Review results"; subtitle `{filename} · {timestamp}`. Export buttons: "JSON" + "PDF report" (both `gbtn2`, download icon) and gradient "Annotated PDF" (pencil icon).
- **Overall risk panel:** left — 152px `ringDraw` gauge showing `6.8` / "out of 10.0" + a "HIGH RISK" pill. Right — "Executive summary" kicker + summary paragraph + a stat strip "11 findings · 3 high risk · 5 agents".
- **Agent cards (5, one per domain — mock renders in a 2-col grid):** top 3px accent stripe in the agent's risk color; header with monogram tile (L/F/T/R/D), agent label, findings count, a risk-level pill; an "Agent confidence" gradient bar with %. Body = list of **expandable findings**:
  - Collapsed row: chevron (rotates 90° when open), finding text, small risk pill.
  - Expanded (`fadeUp`): "{page} · confidence {n}%" meta; a violet-left-border "Source text" quote block; a "Recommendation" block.
  - **Behavior:** one finding expanded at a time (accordion) — clicking a row toggles it (`expanded` state keyed `{agentKey}-{index}`). Wire real data from `FindingsList` / `AgentCard` / `ConfidenceBar` / `RiskBadge`.
- **Data shape:** matches `lib/types.ts` — `AgentResult { agent, domain, findings[], agent_confidence }`, `Finding { finding, risk_level, confidence, page_reference, recommendation, source_text }`. Agent-level risk = highest severity among its findings.

### 5. Dashboard  (`screenshots/04-dashboard.png`)  →  `frontend/app/dashboard/page.tsx`, `components/dashboard/ReviewHistoryTable.tsx`
- **Purpose:** Review history + risk analytics across all reviews.
- **Layout:** header block; 4-col stat cards; `grid 2fr 1fr` (distribution chart + risk filter); full-width history table.
- **Stat cards (4):** top accent stripe + label + big number. "Total reviews" (blue), "Total findings" (violet), "Avg risk score" (pink), "High risk" (orange). Values computed from the review list.
- **Risk distribution:** vertical bar chart, one bar per level (HIGH/MED/LOW) in its risk color, count above, `growBar` grow-in, colored glow. (The real `dashboard/page.tsx` uses **Recharts** `BarChart` — keep Recharts and restyle bars to these colors/glow.)
- **Filter by risk:** stacked buttons — "All reviews" (active = violet-tinted), High / Medium / Low each with a colored dot. Sets `riskFilter` and refetches the list.
- **History table:** columns **Filename · Date · Risk score · Level · Findings · Status**. Filename cell has a file icon; Level is a risk pill; Status is a dot+label pill (complete=green, in progress=blue pulsing, error=red). Rows are clickable → `/review/{review_id}` and hover-highlight. The real component supports **sortable headers** (Filename/Date/Risk Score/Findings) and loading skeletons / empty state — preserve those.

---

## Interactions & Behavior (summary)
- **Nav flow:** Login → (Transition) → Upload; nav bar switches Upload/Review/Dashboard; "Sign out" → Login.
- **Accordion:** Review findings — single-open accordion per the `expanded` key.
- **Hover states:** cards lift; buttons lift/brighten; table & finding rows tint (`rgba(255,255,255,.04)`).
- **Focus:** inputs get violet ring — extend a `:focus-visible` treatment to all interactive elements.
- **Loading:** dashboard table shows skeleton rows while `isLoadingList`; keep for the review page while agents run (the mock's landing chips "3 agents done" hint at a live progress view — the store already models `in_progress`).
- **Reduced motion:** honor `prefers-reduced-motion` (maps to the "Still" preset).

## State Management
Reuse the existing Zustand `store/reviewStore.ts`:
- `reviewList`, `totalReviews`, `isLoadingList`, `fetchReviewList(riskFilter?)` — Dashboard.
- Review detail state + `/api/v1/*` fetches in `lib/api.ts` — Review page.
- Local UI state only for: which finding is expanded (Review), active `riskFilter` + sort field/direction (Dashboard), auth form fields (Login).

## Assets
- **Fonts:** Google Fonts — Plus Jakarta Sans (500–800), Inter (400–600).
- **Icons:** inline SVGs in the mock (upload, download, pencil/edit, mail, file, chevron, users/check/bar-chart for features). Replace with **Lucide** (`lucide-react`) equivalents in code.
- **Google "G" logo:** multicolor inline SVG on the Login Google button.
- No raster image assets — all visuals are CSS gradients, SVG, and generated content.

## Files
- `SOWnia Vivid.dc.html` — the full interactive prototype (all four screens + transition). Open in a browser to click through. All exact copy, colors, SVGs, animations, and mock data live here — it is the source of truth for anything not spelled out above.
- `screenshots/01-login.png … 04-dashboard.png` — reference captures of each screen.
