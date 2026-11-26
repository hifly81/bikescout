# BRAND.md — BikeScout brand, voice and visual contract

Normative for identity, tone, terminology and visual tokens in every user-facing artifact: Streamlit UI, MCP responses, chat planner replies, docs, README, website and agent answers. Code identifiers follow `CODE_STANDARDS.md`; product intent follows `SPEC.md`.

## 1. Positioning and promise

- **One-liner:** "Open-source AI cycling route planner for MTB, gravel, road and e-bike riders" (README).
- **Brand line:** "BikeScout | Tactical Cycling Intelligence" (site).
- **Promise:** turn raw map, weather and elevation telemetry into pre-ride **Tactical Intelligence** — precise setup advice and risk context before leaving the garage.
- **Differentiator:** while other products focus on *where* to go, BikeScout focuses on *how you can thrive on that specific ride, right now*.
- **Audience:** endurance/off-road riders, e-MTB/performance riders, and AI agent hosts (see `SPEC.md` §2).

Do not inflate claims into guarantees of safety, legality or exact prediction.

## 2. Voice principles

| Principle | Meaning | Example |
| :--- | :--- | :--- |
| Tactical | Concise, actionable, mission-oriented | "Carry 1.5 L; refill at km 18." |
| Evidence-first | Name the inputs; no false precision | "Estimated from a 30 km loop, 620 m ascent and 18 °C." |
| Plainspoken | Define jargon once; prefer plain verbs | "Battery estimate assumes Eco mode and 22 °C." |
| Empowering, safety-aware | Give the rider the decision, with clear risk signals | "No-Go recommended: forecast 12 mm rain on saturated soil." |
| Honest | Label estimates and disclose failures | "Weather service unavailable; forecast overlay omitted." |

Tone by surface: MCP responses are neutral and data-first; chat replies are collaborative ("I found a 28 km loop..."); errors are direct, blameless and always include a next step. Avoid hype, exclamation marks and superlatives in functional copy.

## 3. Say / don't say

| Prefer | Avoid |
| :--- | :--- |
| "Tactical Intelligence briefing" | "magic AI plan" |
| "Estimated mud risk: high (12 mm forecast, saturated soil)" | "The trail will be a disaster" |
| "Front: 1.9 bar / 28 PSI for 85 kg rider, 29\" tubeless" | "Use whatever feels right" |
| "Geocoding failed for 'X'. Try a nearby town or provide lat/lon." | "Error!!" |
| "Go/No-Go: No-go — high wind and mud risk" | "You'll probably be fine" |
| "ORS-compatible routing (HeiGIT)" | "Google Maps routing" |

## 4. Canonical terminology

| Term | Rule |
| :--- | :--- |
| **BikeScout** | One word, capital B and S. Never `BIKESCOUT` or `bike-scout` in prose (`bike-scout` is a server name in host configs) |
| **Tactical Intelligence** | Two words, both capitalized; the consolidated briefing produced by a mission |
| **mission** | A ride-planning request; output is a "mission briefing" or "briefing" |
| **overlay** | Optional analysis layer enabled by an `include_*` flag (weather, mud, nutrition, POI, GPX, map, altimetry) |
| **bike type** | Tool values are lowercase `mtb`, `enduro`, `gravel`, `road`, `e-mtb`; prose uses `e-MTB` |
| **profile** | Routing profile (`cycling-mountain`, `cycling-road`, `cycling-electric`, `cycling-regular`), not fitness level |
| **complexity** | Planner difficulty `1–5`, mapped to `3–5` ORS waypoints at the UI→tool boundary; the tool accepts `3–10` waypoints (alias `points`) |
| **ride window** | Recommended time slot for a ride |
| **Go/No-Go** | Readiness verdict; keep hyphens and slash |
| **POI / POIs** | Spell out "Point of Interest" on first use in prose; `POI` is fine in tables and UI |
| **tire setup** | Pressure recommendation in PSI/bar; use "tire" spelling in code-facing copy |
| **battery telemetry** | Estimated `Wh` drain and remaining `%`, not a measured value |
| **TAEL® Mud Reservoir Model** | Keep the registered mark as in README; do not apply ® to BikeScout itself |

Keep local place and trail names verbatim (e.g. Arenberg, Castelli Romani, Shimanami Kaido, Derby) rather than translating them.

## 5. Language rules

- Code comments, docstrings, identifiers and error strings: **English** (`CODE_STANDARDS.md` §2).
- User replies: the user's language; place/trail names stay local.
- Docs: one language per file; existing harness docs are English. Translations must keep headings, tool names, keys and glossary spellings unchanged.
- Never translate tool names, schema keys, environment variables or MCP resource URIs.

## 6. Numbers, units and formatting

- Metric first: `km`, `m`, `kg`, `°C`, `%`, `Wh`, `mm`, `h`; tire pressure as `1.9 bar (28 PSI)`.
- Decimal point; ranges with an en dash (`10–20%`); dates ISO 8601 (`2026-11-25`); local times with timezone when known.
- Coordinates as `lat, lon` in that order, 5–6 decimals.
- Round to decision-relevant precision: distance `0.1 km`, ascent `1 m`, temperature `1 °C`, pressure `1 PSI` / `0.1 bar`, battery `1%`.
- No emoji in structured outputs, errors or logs. 🚴 is the app/site icon only.
- Sentence-case headings; periods in bullets only for full sentences.

## 7. Visual identity

| Surface | Tokens | Source |
| :--- | :--- | :--- |
| Wordmark | `Bike` + `Scout` (site renders "Scout" as neon text); favicon: green `#2D5A27` rounded square with white **BS**; app icon 🚴 | `site/index.html`, `site/images/favicon.svg`, `app.py` |
| Website | Accent `#bef264`; backgrounds `#0f172a`, `#0b0f1a`; dot grid `#334155`; Inter + JetBrains Mono | `site/index.html` |
| App CSS | `--bg #0b1020`, `--bg-soft #121933`, `--card rgba(20,27,52,0.78)`, `--card-2 rgba(30,39,72,0.78)`, `--border rgba(148,163,184,0.16)`, `--text #edf2ff`, `--muted #aeb8d0`, `--primary #7c3aed`, `--primary-2 #22c55e`, `--info #38bdf8`, `--warn #f59e0b`, `--danger #ef4444`, `--radius 18px`; gradient `#0b1020 → #0f172a`; Inter 400/500/600/700/800 | `app_ui_helpers.py` |
| Streamlit theme | `base = "dark"`, `primaryColor #7c3aed` (aligned with app CSS `--primary`), `backgroundColor #000000`, `secondaryBackgroundColor #161b22`, `textColor #e0e0e0`, `hideSidebarNav = true` | `src/bikescout/config.toml` |

Rules: reuse existing tokens for new UI work; do not introduce a fourth accent color. The app surface (CSS tokens + Streamlit theme) now shares `#7c3aed` as its primary; the site keeps `#bef264` as its own neon accent by design, and the favicon keeps `#2D5A27`. Never change the wordmark, tagline or an established palette without approval (`AGENTS.md` §5).

## 8. Legal and attribution

- License: AGPL-3.0-only; keep the Python file header from `CODE_STANDARDS.md` §1 and the AGPL mention in public docs.
- Data credits: ORS-compatible routing/POI by HeiGIT; OpenStreetMap contributors (ODbL) via Nominatim; Open-Meteo (CC BY 4.0). Preserve these attributions in README, site and published reports.
- Do not imply trademarks or endorsements that are not documented.

## 9. Copy checklist (before shipping any user-facing text)

- [ ] Terminology matches §4; tool names, keys and env vars unchanged.
- [ ] Units and rounding follow §6; dates are ISO-formatted.
- [ ] Estimates are labeled with inputs; errors give a next step; no fabricated data.
- [ ] Voice follows §2/§3; no unverifiable claims.
- [ ] No new visual tokens; palette follows §7.
- [ ] License and data credits intact; no secrets exposed.
