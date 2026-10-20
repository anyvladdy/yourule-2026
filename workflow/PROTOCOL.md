# PROTOCOL.md

Reader: AI agents. Goal: exact rules for planning, doing and reviewing task cards. Human version: `workflow/README.md`.
Read after `AGENTS.md` §0. Workers need §1–§3 only.

## 1. Roles and write permissions

| Role | Agents | Must | Must not |
|---|---|---|---|
| Planner | Claude (drafts, decides), Codex (one critique per stage → `stage<N>/PLAN_CRITIQUE.md`) | write cards; settle disagreements | do card work in R1/R2 |
| Worker | dsh, Gemini (`agy`), OpenCode + Ollama (qwen3:8b, gemma4, gemma3:4b) | write `out/`, `HANDOFF.md` in own card folder; update own BOARD row | write anywhere else; commit |
| Reviewer | Codex (facts & format), Claude (content, verdict) | write `REVIEW_R<n>.md`; Claude integrates accepted outputs (keep card/row IDs); Codex runs script checks | rewrite worker outputs in R1/R2 |

Assignment defaults:
- dsh: web research, verification, timelines, official documents, analysis scripts (later stages).
- Gemini: web search breadth, long documents, Russian drafting (later stages).
- Local models: no web; input = one short file; mechanical text tasks. One model loaded at a time (24 GB RAM).

## 2. Card lifecycle

States: `ready → in_progress → review_R1 → fix_R2 → review_R2 → accepted → integrated`; or `escalated`; `waiting`/`draft` before ready.
- Worker sets `in_progress` on start, `review_R1` (or `review_R2`) on handoff.
- Reviewers set all other states.

Sequence:
1. Planning: Claude drafts cards → Codex critiques once → Claude settles. Second critique only on material disagreement.
2. R1: worker executes card → Codex fills "Facts and format" → Claude fills "Content" + verdict.
   - `accept` → Claude integrates → `integrated`.
   - `fix` → numbered atomic fix list (F1…) → `fix_R2`.
3. R2: worker fixes only F-items, appends "For R2" to HANDOFF → review of F-items + their knock-on effects
   (IDs, counts, dependent conclusions). New serious errors found by anyone are reported anyway.
   - `accept` → integrate.
   - items still failing → `escalated`; REVIEW_R2 names owner per item (Claude|Codex). No R3 for workers.
4. Stage gate: all cards `integrated` → Claude + Codex write ≤ 20-line summary in BOARD.md (index of accepted
   artifacts, IDs, open questions, decisions) → Claude merges stage branch into `main` → next stage cards.

Cards in one stage may run in parallel. A card may start when its listed inputs are `accepted`.

## 3. Worker procedure

1. Read: `AGENTS.md` §0 → this file §1–§3 → your `CARD.md` → only the inputs it lists.
2. Set BOARD row `in_progress`.
3. Produce outputs in `out/` exactly as the card's schema. Respect time box and size caps (caps are ceilings).
   Discovery stops after 5 consecutive searches with nothing new.
4. Write `HANDOFF.md` from `workflow/templates/HANDOFF.md`: done (files + row counts), self-check per acceptance
   criterion (honest ticks; explain unticked), deviations, unsure items with queries tried.
5. Set BOARD row `review_R1`. If `REVIEW_R1.md` exists, you are in R2: fix only its F-items, set `review_R2`.

## 4. Review procedure

Codex, "Facts and format":
- Run script checks on whole files every round: parse validity, schema columns, unique IDs, row counts, duplicates,
  regex tests where relevant.
- Check every acceptance criterion.
- Critical rows: check 100%. Critical = heritage status, preserved/demolished status, official decisions,
  roadmap dates, any number destined for the report. Stage 0: T04 C01–C08, all of T08.
- Other rows: random sample per output file, 20%, min 5, max 15, ≤ population, stratified by source type.
  Record sampled IDs.
- Sampled row fabricated or substantively wrong → F-item "re-verify all rows of <file>". Formatting fault → F-item for those rows.
- Self-check ticks are triage only; never skip critical rows because of a tick.

Claude, "Content" + verdict:
- Read Codex's section first; do not repeat its checks.
- Assess: coverage gaps, source bias, usefulness for C1–C5, what later stages need.
- Write verdict `accept | fix | escalate` and the final F-list.

## 5. Files

```
workflow/BOARD.md                     card rows, rounds, states, stage summaries
workflow/prompts/worker.md, codex.md  launch prompts
workflow/templates/                   CARD.md, HANDOFF.md, REVIEW.md
workflow/stage<N>/README.md           human summary of the stage (keep in sync with cards)
workflow/stage<N>/T<NN>_<slug>/       CARD.md (frozen once work starts), out/, HANDOFF.md, REVIEW_R1.md, REVIEW_R2.md
```

## 6. Token economy rules (do not trade away quality)

1. Read only listed inputs. Cards quote the rules they need.
2. Structured outputs (CSV/YAML with fixed columns), not prose.
3. HANDOFF ≤ 30 lines; stage summary ≤ 20 lines.
4. Split review lenses; sampling except critical rows.
5. Atomic F-lists; R2 scope = F-items + knock-on effects.
6. Reference paths; never paste readable files. Agents without file access get one bounded input file.
7. Mechanical work → local models or scripts; planning/judgement → Claude/Codex.
8. One plan critique per stage.
9. Reuse verified IDs across cards instead of re-researching.
10. Stop on documented criteria, not quotas.
11. Validation, counting, ID generation, dedupe → scripts.
