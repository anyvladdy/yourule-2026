# Final check of the report — brief for Codex (2026-10-29)

Reader: Codex. Goal: a last review of the assembled report before submission on 2026-11-01.
Write the result to `workflow/stage1/REVIEW_CODEX_2026-10-30.md` in Russian, same format as
`REVIEW_CODEX_2026-10-29.md`: verdict `ready` | `fix`, then findings F1… with file, problem, fix. Do not edit
`deliverables/` or `docs/`; Claude applies the fixes. Read AGENTS.md §0, §2, §6, §7 first.

## What changed since your review of 29.10

Your F1–F10 and how each was closed: D-44–D-47 (wording, fact recheck, human check of labelling, collusion
share), D-48–D-51 (council, cats, scheme fallback, district meetings, former tenants), D-52 (Word file, appendices,
budget rounding). The report is `deliverables/Elektrozavod_report.docx`, built from `deliverables/drafts/` by
`src/report/build_docx.py`; the calendar is also a separate file `deliverables/appendix_timeline.pdf`.

## What to check

1. Limits: main text ≤ 10,000 characters with spaces and ≤ 8 pages in Word, Times New Roman 12, title page and
   appendices excluded. Run `src/report/check_length.py` and `src/report/build_docx.py`; open the .docx in Word if
   you can and count the pages of the main text.
2. Every number and date in the main text against its source: `docs/report_fact_check.csv` (F01–F29),
   `reports/tables/`, `docs/analysis_findings.md`, `deliverables/budget.csv`, `deliverables/roadmap.csv`.
   Section 6 against `budget_check.py`; section 7 and appendix Ж dates against the roadmap.
3. Appendices В, Г, Е are generated (`src/report/build_appendices.py`): rerun and confirm they match the tables.
4. R10: nothing implies more is preserved than the approved project preserves. §7: no astroturfing, hidden
   advertising, pressure on critics or removal of criticism (check the cats, district meetings, launch message).
5. Feasibility (C5): start before 01.11, five working days per client approval, New Year holidays, budget
   9,965,595 RUB of 10,000,000 with 34,405 left and a 905,963 reserve; costs left to the client (vet care, first
   right to apply for studios) are named as such.
6. Style §6 in the main text and appendices: plain language, one name per concept, banned words, abbreviations.

## Claude's self-review against the criteria (for you to confirm or reject)

| Criterion | What the report has | Known weak points |
|---|---|---|
| C1 context and logic | situation → concept «Подлинное — на виду» → strategy; facts reopened 29.10 | analogue cases not used (H7 open); causes of attention spikes shown as timing only |
| C2 audiences | appendix А: 11 groups with position, motives, influence, engagement, approach, speaker | positions come from social media reactions, not people; the November survey fills this |
| C3 detail | 78 budget lines with sources, 48 calendar steps with owners, results and KPIs | strategy fee, scheme, project page and the district meeting moderator (75,000) are assumptions |
| C4 negative agenda | three main accusations (94% of critical reactions with a named line), answers, risks, signals, decision options for the client | who starts and who spreads the criticism (H2) not analysed |
| C5 feasibility | launch text ready (appendix Ж), fallback for the scheme, approvals and holidays in the calendar | budget 99.7% used; vet care and the studios decision depend on the client |

Open items not for you: team names on the title page (the user), page count in Word (the user, if you cannot).
