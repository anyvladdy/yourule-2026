# Decisions log

Reader: people and agents. Goal: record each decision with its reason.

Format: `D-NN | date | who | decision | reason`.

- D-01 | 2026-10-20 | user | No parsing and no parser code in stage 0; discovery is manual browsing/search only | keep stage 0 light; parsers planned after sources are known
- D-02 | 2026-10-20 | user | Plan by Claude + Codex, work by dsh / Gemini / OpenCode+Ollama, review by Claude + Codex; failing items after 2 review rounds go to Claude/Codex | use different models' views while keeping each agent's load small
- D-03 | 2026-10-20 | Claude | Reviews use split lenses (Codex: verification, Claude: substance) with spot-checks of 20% of rows (min 5, max 15) | fewer tokens without reducing coverage; any failed sample triggers a full re-verification
- D-04 | 2026-10-20 | Claude | T04 (reality check) runs first | the brief's 2026 scenario may be partly hypothetical; this decides whether we use real data or proxies
- D-05 | 2026-10-20 | Claude (after Codex PLAN_CRITIQUE) | Split old T03: media/criticism lines → T03 (Gemini); official docs, developer statements, building matrix → new T08 (dsh, checked in full). T05 moved to Gemini and cut to 4–6 cases. T06 limited to core+site_context in 2 batches. T07 kept as draft until inputs are accepted | Codex proposals 2, 10, 12, 13, 14–18
- D-06 | 2026-10-20 | Claude | Added provenance rule (accessed date, fact/brief/proxy/inference labels) to AGENTS §0; critical rows checked in full; R2 may report new serious errors; mechanical checks by script; workers may edit their own BOARD row | Codex proposals 6, 19, 21, 22
- D-07 | 2026-10-20 | Claude | Deferred to the stage-0 gate (not worker cards): evidence map, audience coverage matrix, hypothesis specification, stage-1 sampling plan, feasibility follow-ups | Codex proposals 1, 3, 4, 5, 7; these are planner work and need stage-0 outputs first
- D-08 | 2026-10-20 | Claude (user request) | Each document has one goal and one reader. Paired docs: README.md / AGENTS.md, workflow/README.md / workflow/PROTOCOL.md, workflow/stage<N>/README.md / cards. Records (board, decisions, hypotheses) are shared. Agent-doc changes that affect people update the human pair in the same commit | people find model-written docs hard to read; agents need exact, terse rules
- D-09 | 2026-10-20 | user + Claude | T06 moved from OpenCode/qwen3:8b to Codex, done with a pymorphy3 script and automatic regex tests; local models keep T07 and later small labelling batches | an 8B model is unreliable at Russian phrase inflection and regex; failures would reach Codex after two rounds anyway
- D-10 | 2026-10-20 | user + Claude | Submission deadline 2026-11-01. Run research and report tracks in parallel; stage-0 cards run in parallel (T01 and T03 start now, T08 after T04 handoff, T05 after T02 handoff); stages 1 and 2 merged and limited to top sources; schedule in BOARD.md | 12 days left; sequential stages would not fit
- D-11 | 2026-10-22 | user + Claude | Codex is out of usage limits: Claude does both review parts (facts and content) and is the fallback instead of Codex until limits return | the user reported the limits; reviews cannot wait under the deadline
- D-12 | 2026-10-22 | Claude | Outlets designated undesirable in Russia (e.g. Meduza) are never the only source and are not cited in the report (AGENTS R12) | the client is a Moscow developer; citing them is a legal and reputational risk. T04 R1 found Meduza as the only source for 4 of 8 claims
