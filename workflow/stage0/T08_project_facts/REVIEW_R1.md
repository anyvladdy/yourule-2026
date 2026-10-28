# REVIEW T08 — R1

Codex is out of usage limits (D-11), so Claude did both parts of the review.

## Facts and format (Claude, standing in for Codex)
Critical card: every row checked. Opened on 2026-10-22: mos.ru law page (O01), Москвич Mag 2026-08-04 (O02, O03),
archi.ru project card (O05, broken encoding; years 2022/2025, Nowadays and Syntaxis legible), mskagency (S01),
Афиша Daily (S02 and matrix rows on interiors, capsule, monument), m24 2026-06-26, 07-17, 08-24, 09-09, 09-30 (S03–S07),
restate.ru 2026-09-10 (строение № 11). Extra sources opened for the review: Москвич Mag 2026-09-08
(https://moskvichmag.ru/?p=522349), MSK1 2026-09-08 (https://msk1.ru/text/gorod/2026/09/08/76631945/).
All 7 statements match their sources, including every number in S03. No Meduza-only facts (R12 respected).

| Criterion | Pass? | Note |
|-----------|-------|------|
| A1 | yes | all URLs open; `accessed` present |
| A2 | partly | statuses follow cited evidence, except строение № 11, where two media reports of dismantling were missed (C2) |
| A3 | partly | корпус № 10 says "no conflict", but Москвич Mag calls it "один из исторических корпусов" while the company says 1953, auxiliary (C1) |
| A4 | partly | no invented documents or quotes. "Г. Шиханов" in the ensemble row has no cited source; Афиша Daily names only Евланов (C3) |

## Content (Claude)
- The matrix gives the report its limits (AGENTS R10). No building has documented protection: ДКН told the court the
  site is "просто здание". Everything marked preserved (facades on main streets, entrance group, towers, portals,
  artifacts) rests on company statements reported by ТАСС, m24 and Афиша Daily. There is no project document.
  The report may say "the company has announced it will keep…", not "is kept".
- The project mix changed in the company's own words: "финансово-деловой центр «Система-Сити»" (2025-09) versus
  more than 287,000 m² of housing and about 17,000 m² of offices out of more than 800,000 m² (2026-06). Critics' "commercial
  development" line will use this. It goes into the message-gap analysis and the answers to criticism.
- The company already runs several actions a strategy would propose: an expert group on heritage (set up on a proposal
  from АФК «Система» shareholders), research by «МВ-ПРОЕКТ», an artifact inventory with two Moscow historians. Little of
  it reaches the public as proof. This is a direct input for the strategy section.
- Gaps the report has to state as such: ГЗК decision, approved ППТ, building-by-building scheme, primary press releases
  (corporate site not reachable). `reaction_seen` is empty in all rows; stage 3 fills the message gap instead.

## Verdict: accept, with corrections applied by Claude at integration (D-13)
The four corrections below use sources the reviewer already opened. The worker output stays unchanged; the corrected
copy is `docs/project_facts/`.

## Corrections applied at integration
- C1 building_matrix «Корпус № 10»: conflict shown. Company (S06): 1953, auxiliary, outside the ensemble. Москвич Mag
  2026-09-08: "один из исторических корпусов". Meduza 2026-08-07 reported a five-storey building near проходная № 4
  demolished in early July, possibly the same one (only source: Meduza).
- C2 building_matrix «Строение № 11»: status `planned_demolished`; dismantling under way per MSK1 and Москвич Mag
  2026-09-08 ("корпус середины XX века с неоклассическим фасадом"); the company has not named it.
- C3 building_matrix ensemble row: "Г. Шиханов" removed (no source opened); architect Г. Евланов per Афиша Daily.
- C4 official O02: "около 1,5 тыс." replaced with the two figures by source: "более полутора тысяч" (Москвич Mag
  2026-08-04) and 1,322 (Москвич Mag 2026-07-08, https://moskvichmag.ru/?p=510124).
