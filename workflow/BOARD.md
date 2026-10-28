# Board

Reader: people and agents. Goal: who has which task and its status. Rules: `workflow/PROTOCOL.md` (agents), `workflow/README.md` (people). Workers update only their own row.

## Deadline: submission 2026-11-01. Schedule (D-10)

| Dates | Research track (workers) | Report track (Claude + Codex) |
|-------|--------------------------|-------------------------------|
| Oct 20–21 | Stage 0: all discovery cards, run in parallel | Report outline with character budget; budget and roadmap skeletons |
| Oct 22–24 | Stages 1+2 together: small collectors for the top sources only, cleaning | Audience map and public-image concept drafts from stage-0 facts |
| Oct 25–26 | Stage 3: analysis (stance, criticism lines, actors, timeline) | Strategy and answers to criticism, updated with findings |
| Oct 27–28 | Gap-filling research on request | Budget and roadmap finalised |
| Oct 29–30 | Fact check of every number in the report | Russian text, .docx, length and format checks |
| Oct 31 | | Buffer, final review, submit |

Speed rules for this deadline: cards run in parallel whenever their inputs exist (two sessions of the same agent are fine);
review happens within hours of a handoff; the gate summary is written the same day.

## Stage 0 — Scoping and source discovery (no parsing)

| Card | Title | Worker | Starts when | Round | State | Fallback |
|------|-------|--------|-------------|-------|-------|----------|
| T04 | Reality check C01–C08 + timeline | dsh | now (first) | R2 | review_R2 | Claude |
| T02 | VK + petitions | Claude (was Gemini, D-16) | now | R2 | review_R2 | Codex |
| T06 | Keyword forms + tested regexes | Codex | now | R1 | review_R1 | Claude |
| T08 | Official docs, developer statements, building matrix | dsh | T04 handoff | R1 | review_R1 | Claude |
| T01 | Telegram + video sources | dsh (2nd session) | now | R1 | review_R1 | Claude |
| T03 | Media + criticism lines | Claude (was Gemini, D-16) | now | R2 | review_R2 | Codex |
| T05 | Analogous cases (4–6) | dsh | now | R1 | review_R1 | Claude |
| T07 | Merge into registry format | OpenCode/gemma4 | card finalised after T01–T03, T08 accepted | – | draft | Claude |

Load: dsh T04 + T01 in parallel, then T08 and T05; Gemini T02 + T03 in parallel;
Codex T06 (script-based), local model T07. Planner work: Claude integrates; Codex runs scripted checks.

## Повторный фактчекинг Codex, 26–27 октября 2026

Факты и формат проверены; результаты и замечания: [сводка](stage0/FACTCHECK_CODEX_2026-10-26.md).
T01–T06 и T08 возвращены на рассмотрение Claude в прежнем раунде. Исходные выходы сохранены.
Новые замечания не сняты прежними статусами `accepted`/`integrated`; третий раунд исполнителям не назначен.
T07: проверка отложена до появления результата слияния.

## Stage 0 review, 2026-10-28 (Claude)

- Cards T01–T06, T08 are done; all are back in review after the Codex re-check. Its fixes are not yet applied to `docs/`:
  T03 criticism labels incomplete (counts unusable until relabelled), T04 dates and attribution, T05 chronology and
  outcome claims, T06 saved output has 22 terms vs 21 in config and the generator fails, T08 promises vs document status,
  `docs/audiences.md` counters without observation dates. `validate_factcheck.py` runs clean (17 CSV).
- Gate: 2 of 7 items closed. Merged into `main` before the gate at the user's request (D-18).
- Behind the D-10 schedule: stages 1–3 had no data or code by Oct 28; report sections 1, 4, 5, 6 not drafted;
  budget has 62 lines, none priced.

## Stage 0 gate (Claude + Codex)
- [ ] All cards `integrated` (or escalated items finished by Claude/Codex)
- [ ] `config/sources.yaml` and `config/keywords.yaml` updated and validated by script
- [x] Proxy decision recorded in `docs/decisions.md` (from T04/T08: where real data exists, where we use proxies)
- [ ] **Deliverable evidence map** (`docs/evidence_map.md`): for each of the 6 report sections — evidence ids in hand,
      open questions, owner, acceptance check
- [x] **Audience coverage matrix** skeleton (`docs/audiences.md`): residents, preservationists, architects, current tenants
      and cultural users of the site, journalists, officials/deputies, Etalon employees/investors, prospective
      tenants/buyers, wider Moscow public — evidence vs inference, gaps, how to validate later
- [ ] Hypotheses H1–H7 specified per `docs/hypotheses.md` header
- [ ] Stage-1 plan inputs: observation window, platform coverage, keyword pilot rule, ToS/access notes per source
- [ ] Follow-ups for later stages recorded: cost benchmarks, client approval times, spokesperson availability,
      campaign KPI baselines, 8-page/10,000-character/render checks for the report

### Stage 0 summary
_(≤ 20 lines, written at the gate: an index of accepted artifacts, ids, uncertainties and decisions)_

## Stages 1–3 — cut collection, processing and analysis, Oct 28–30 (D-19, D-20, D-21)

Branch `stage-1-collection`. No video content; residents' voices also from district party newspapers and Telegram chats.

| Task | Owner | When | State |
|------|-------|------|-------|
| YouTube: video search + all comments, official API (`src/collectors/youtube_comments.py`) | Claude | Oct 28 | done: 80 videos, 10,926 comments; see `docs/data_cards/corpus_manifest.md` |
| Telegram channels from T01: the user's parser ported to `src/collectors/telegram_web.py`, public pages, no login (D-23) | Claude | Oct 28–29 | done: 13 channels (11 from T01, 2 from T13), 140 posts, 1,464 comments |
| T13 District newspapers and residents' chats: find and read (`workflow/stage1/T13_district_voices`) | dsh (2nd session) | Oct 28–29 | accepted |
| T12 Price benchmarks for budget lines (`workflow/stage1/T12_price_benchmarks`) | dsh | Oct 28–29 | accepted |
| VK: global post search + communities, manual login in Brave incognito (`src/collectors/vk_web.py`) | Claude | Oct 28 | stopped after logout (D-26): 303 posts, 1,360 comments; 13 communities not covered |
| Etalon's own channels: Telegram (collected), project site and press statements (T08) for the message gap; VK community not collected (D-26) | Claude | Oct 29 | done: `docs/etalon_channels.md` — no posts about the site in own channels during the conflict |
| Wordstat and Google Trends export; petition signature snapshot (`Tasks_for_humans.md` 1–3) | user | Oct 28–29 | ready |
| T14 Tenants, cultural spaces, deputies: public statements (`workflow/stage1/T14_tenants_deputies`) | dsh | Oct 28–29 | review_R1 |
| T16 Dzen: Selenium pilot, full run only if useful (`workflow/stage1/T16_dzen`) | dsh (2nd session) | Oct 28–29 | in_progress |
| T15 Media: relabel all 27 T03 articles with `docs/codebook.md` (`workflow/stage1/T15_media_relabel`) | Codex or local Qwen (user decides) | Oct 29 | ready |
| T11 Processing: raw YouTube + Telegram → `data/processed/corpus.parquet` (`workflow/stage1/T11_processing`) | Codex | Oct 28–29 | in_progress: YouTube; Telegram pending full collection |
| T06 fix: saved variants (22 terms) vs config (21), generator error | Codex | Oct 29 | not started |
| Labelling: codebook `docs/codebook.md` v0 written; Claude 50%, Codex 25%, dsh 25%; user re-checks a random sample from each (D-20) | Claude, Codex, dsh, user | Oct 29–30 | codebook v0 ready; labelling starts after T11 |
| Analysis: timeline vs T04 events, stance, criticism lines, actors, message gap | Claude | Oct 30 | not started |

In parallel: stage-0 fixes in `docs/`, report sections 1, 4, 5, 6. Budget with prices and the launch line before
Nov 1 comes first (Codex review P13).

Codex review of Oct 28 and Claude's answer to each point: `workflow/stage1/REVIEW_CODEX_2026-10-28.md`,
`workflow/stage1/REVIEW_CODEX_2026-10-28_REPLY.md`.
Transcripts are not collected: `captions.download` needs OAuth and the right to edit the video (D-22).

## Later stages (cards written at each gate, not now)
4. Synthesis
5. Budget and roadmap
6. Report
