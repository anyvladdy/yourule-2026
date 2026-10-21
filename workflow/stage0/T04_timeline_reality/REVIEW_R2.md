# REVIEW T04 — R2

Claude did both parts (D-11). Scope: F1–F7 and what they touch.

## Facts and format (Claude, standing in for Codex)
Script checks: both CSVs parse, columns unchanged, 8 claims and 18 events, timeline sorted, no Meduza URL in any
`source_url` of reality_check.csv; the 5 timeline rows still on Meduza say "(только источник: Meduza)" (5 of 5).
New sources opened on 2026-10-22: vm.ru 2026-07-17 (C05, "безусловно сохранит входную группу и фасады", ТАСС),
daily.afisha.ru 2026-06-21 (C01, ГЗК row), theblueprint.ru 40411 (2026-06-24 row; page shows both 23.06 and 24.06),
archnadzor.ru 2026-07-27 (complaint, claimants and respondents as stated), Москвич Mag 2026-07-08 (court, 1322, ~150 people).

| Item | Fixed? | Note |
|------|--------|------|
| F1 | yes | C03 confirmed; three mentions agree |
| F2 | yes | both counts with sources, plus Архи.ру's |
| F3 | yes | |
| F4 | yes | Архнадзор named by its own release. The release cites article 17 of the Moscow heritage law without the number; mos.ru confirms it is law № 24 (T08 O01) |
| F5 | yes | confidence `low`; Афиша Daily replaces the empty Рамблер page |
| F6 | yes | Газета.ру and the lease notice not found; marked "only source" |
| F7 | yes | |

## Content (Claude)
No new problems. The four Meduza-only events (lease notice, July demolition, Borodin 2026-07-24, and Meduza's own
publications) stay internal; the report does not use them.

## Verdict: accept
## Integration
`out/reality_check.csv` and `out/timeline.csv` copied unchanged to `docs/project_facts/`.
