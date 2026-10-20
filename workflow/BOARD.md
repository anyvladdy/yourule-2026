# Board

Protocol: `workflow/README.md`. Workers update only their own card's row.

## Stage 0 — Scoping and source discovery (no parsing)

| Card | Title | Worker | Starts when | Round | State | Fallback |
|------|-------|--------|-------------|-------|-------|----------|
| T04 | Reality check C01–C08 + timeline | dsh | now (first) | – | ready | Codex |
| T02 | VK + petitions | Gemini | now | – | ready | Codex |
| T06 | Keyword morphology (2 batches) | OpenCode/qwen3:8b | now | – | ready | Codex |
| T08 | Official docs, developer statements, building matrix | dsh | T04 R1 review done | – | waiting | Claude |
| T01 | Telegram + video sources | dsh | T04 handed off (can run before T08 if T08 waits) | – | waiting | Codex |
| T03 | Media + criticism lines | Gemini | after T02 handoff | – | waiting | Claude |
| T05 | Analogous cases (4–6) | Gemini | after T02 + T03 handoffs | – | waiting | Claude |
| T07 | Merge into registry format | OpenCode/gemma4 | card finalised after T01–T03, T08 accepted | – | draft | Codex |

Load: dsh 3 cards in sequence (T04 → T01 → T08), Gemini 3 in sequence (T02 → T03 → T05),
local models 2 short batched cards. Planner work: Claude integrates; Codex runs scripted checks.

## Stage 0 gate (Claude + Codex)
- [ ] All cards `integrated` (or escalated items finished by Claude/Codex)
- [ ] `config/sources.yaml` and `config/keywords.yaml` updated and validated by script
- [ ] Proxy decision recorded in `docs/decisions.md` (from T04/T08: where real data exists, where we use proxies)
- [ ] **Deliverable evidence map** (`docs/evidence_map.md`): for each of the 6 report sections — evidence ids in hand,
      open questions, owner, acceptance check
- [ ] **Audience coverage matrix** skeleton (`docs/audiences.md`): residents, preservationists, architects, current tenants
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
