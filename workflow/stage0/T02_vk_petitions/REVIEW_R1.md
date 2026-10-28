# REVIEW T02 — R1

## Facts and format (dsh, standing in for Codex; D-16)
Sample checked: P01, P02, P03 (3 of 3 rows, all petitions) + `vk.csv` (header only)
Opened 2026-10-22, HTTP 200: P01 letter page and its counter page; P02 petition page (text, starter,
date and count read through the r.jina.ai text proxy of the same URL — the direct fetch returns only
navigation); P03 press release; the Активатика page cited in P01's note.

| Criterion | Pass? | Note |
|-----------|-------|------|
| A1 | yes | 3/3 rows have a URL that opens now and `accessed` = 2026-10-22. |
| A2 | no | `vk.csv` has a header and 0 rows, so there is no row to test against `relevant_post_url` / `priority`. The card's VK output is empty. See F1. |
| A3 | yes | P01 counter page: «На данный момент подписались: 19700» — row says 19700. P02: «3,682 / Verified signatures» — row says 3682. P03 publishes no number, row says «не указано». P01's «около 2 820» start figure is confirmed by Активатика 26.06.2026 («около 2820 подписей»). |
| A4 | partial | change.org, general web search and the brief's «> 20 000» question are covered: the largest single petition is 19 700, and the Reuters copy (T03 A22) confirms «over 21,000» for two petitions, which matches P01 + P02. VK is not covered, the same gap as A2. HANDOFF states both honestly. |
| A5 | yes | No duplicate `pet_id` or URL; P01 (archi.ru letter) and P03 («Яблоко» paper appeal) are different campaigns; every field I checked is on the page. |

Format: 12 columns per row, 3 rows, valid UTF-8 CSV, quoting correct, header matches the card schema.

Rows checked field by field:
- P01 — title exact («О сохранении исторических зданий Электрозавода и профессиональное обсуждение
  проекта. Сбор подписей»); date 25 Июня 2026; addressees Путин and Собянин are both named in the
  letter; demands match («в подлинном материале», обсуждение профессионалами и общественностью,
  «рассекречивание»); signature count exactly 19700.
- P02 — title exact; «Petition created on March 13, 2025»; starter is a private individual, correctly
  not named (R5); all three demands are in the text (ОКН status for the whole complex, no skyscrapers
  on or next to the site, publish the fire examination); no decision maker is named on the page, so
  «не указан» is right.
- P03 — page dated 8 July 2026, collection from 7 July, office Пятницкая, 31, стр. 2; demand
  («признание исторической ценности» + «государственная охрана») and addressees (власти и застройщик)
  match; no count published. `title` is a description, not the published headline — see F2.
- `vk.csv` — 11 columns, header matches the card schema, 0 rows.

Minor, not an item: on the counter page the headline shows 19700, but the visible signature list stops
at entries dated 26.07.2026. The row copies the displayed count, which is what A3 asks for; whoever
re-uses the series should take the headline figure and its date, not the last list entry.

## Content (Claude)
- Claude was the worker on this card, so the content check is limited; dsh's facts check is the independent part.
- Enough for the report: the brief's "more than 20,000" holds only as two petitions together (Reuters); the largest single one
  has 19,700. The report should say "more than 21,000 signatures under two petitions" with the source.
- The petitions' demands differ: P01 asks for preservation in authentic material and an open professional discussion (achievable
  in part); P02 and P03 ask for legal protection (outside the company's power). The strategy answers P01's demand directly.
- VK moves to stage 1 (D-17); stage 1 also snapshots P01 and P02 counts on a schedule.

## Verdict: accept (R2 fixes F1, F2 applied by the worker; mechanical, checked by Claude)

## Fix list (numbered, atomic; R2 touches only these)
- F1 A2/A4, `out/vk.csv`: 0 rows, so the VK half of the card is absent and A2 cannot pass. Fixed when
  either `vk.csv` holds rows with an opened post URL per the schema, or the card is amended in writing
  (Claude, this round) to move VK discovery to stage 1 and HANDOFF records that amendment as a decision.
  Do not invent groups to fill the file.
- F2 P03, `title`: the value «Обращение Московского «Яблока» за сохранение комплекса Электрозавода»
  is a description; the published headline is «Яблоко» объявило сбор подписей за сохранение
  Электрозавода – редкого памятника промышленности, который вот-вот демонтируют, and no document
  carries the current value. Fixed when `title` quotes the headline or `note` says the title is
  descriptive because the paper appeal has no published title.

## Escalation (R2 only): item → owner (Claude|Codex)
