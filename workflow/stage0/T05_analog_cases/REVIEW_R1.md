# REVIEW T05 — R1

Codex is out of usage limits (D-11), so Claude did both parts of the review.

## Facts and format (Claude, standing in for Codex)
Script: `cases_summary.csv` parses, 5 rows, 7 columns, values of `conflict_level` and `outcome_for_developer` from the card lists.
Sample (4 of 12 sources, one per Russian case), opened 2026-10-22: archnadzor.ru 2021-10-25 (Бадаевский: buildings, 19 000 / 2 000,
"один из самых циничных", status "частями"), dp.ru 2024-12-26 (Канатный цех: Setl Group, ВШЭ, «Белая книга»), newhollandsp.ru
2016-06-30 (first stage, park instead of a new building, "никогда не будет закрываться"), archi.ru 2016-04-08 («Большой город»,
passage to Винзавод, Нижний Сусальный for День города-2015, "соавторами"). All match.

| Criterion | Pass? | Note |
|-----------|-------|------|
| A1 | yes | 5 cases, 4 in Russia |
| A2 | partly | 2+ URLs each, but New Holland and Battersea have one source read in full; «Арма» has two texts from one outlet. Facts and inference are labelled |
| A3 | partly | Бадаевский is `better`, but by the card's definition `better` needs the conflict to subside, and the case's own text says it did not (C1) |
| A4 | yes | no invented facts found. One wording goes beyond the source: dp.ru does not name the customer of the restoration, it says Setl Group did it (C2) |

## Content (Claude)
- Бадаевский is the closest analog: Moscow, demolition of heritage under a city commission decision, high conflict, project built.
  Lesson for the report: a scheme published after demolition does not repair trust; for Электрозавод part of the site is already
  gone, so the scheme must come before the main works in March 2027. Arkhnadzor also reports that most hearing supporters were
  developer staff: a direct argument against any staged support (AGENTS §7).
- New Holland and «Арма» give the positive mechanics: dated, phased openings; temporary public programmes before the plan; opening
  the territory as a route. They had low conflict, so they show what works, not how to calm a high conflict.
- Battersea adds little: no data on the developer's communication. Keep it out of the report.
- Gap: the cases critics themselves cite (Военторг, Детский мир; Гершман in T03 A05) are not covered. They matter for answering the
  "fake reproduction" line. Gap-filling on Oct 27–28 if time allows.

## Verdict: accept, with corrections applied by Claude at integration (D-13)
- C1 Бадаевский `outcome_for_developer`: better → mixed (project built; conflict and reputational criticism continue).
- C2 Канатный цех: "заказчик работ — Setl Group" → "реставрацию выполнила Setl Group (dp.ru)".
Integrated copies: `docs/analog_cases.md`, `docs/analog_cases.csv`.
