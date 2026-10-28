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

## Later stages (cards written at each gate, not now)
1. Collection: collectors + small validation pilots (planned by Claude + Codex after stage 0)
2. Processing
3. Analysis
4. Synthesis
5. Budget and roadmap
6. Report
