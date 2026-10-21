# REVIEW T04 — R1

Codex is out of usage limits (D-11), so Claude did both parts of the review.

## Facts and format (Claude, standing in for Codex)
Script checks (whole files): both CSVs parse; columns match the card; C01–C08 present once each; timeline sorted,
18 rows, 0 duplicate events; every `accessed` = 2026-10-22.
Sample checked: all 8 claims (critical) and all 18 timeline rows. All 10 distinct source URLs were opened on 2026-10-22,
except reuters.com (blocked for the reviewer; checked through the syndicated copy at english.aawsat.com, same text,
credited to Reuters) and electrozavod-etalon.ru (TLS certificate issued for another domain, `*.lpmotortest.com`;
C07's reading of it could not be checked).

| Criterion | Pass? | Note |
|-----------|-------|------|
| A1 | yes | 8 of 8 claims have a status |
| A2 | partly | URLs open and mostly support the rows. C03 is wrong: a source stating > 20,000 exists (F1). archi.ru/print/news/102373 renders with broken encoding; date 25.06.2026 confirmed |
| A3 | partly | No invented sources or quotes found; all quotes checked in C01, C02, C04, C05, C06 appear in the sources. Two attributions go beyond the source (F3, F4); two conflicts are shown as single facts (F2, F5) |
| A4 | yes | sorted, no duplicates |
| A5 | yes | five events with the metric or "no comparable metric"; event 4 changes with F1 |

## Content (Claude)
- The core finding holds: the brief's scenario is documented in public sources. Real data, not stand-ins, can carry
  most of the report. This goes into the stage-0 proxy decision.
- C03 decides a number the report uses. Reuters (2026-07-31) reports two petitions with over 21,000 signatures together;
  the archi.ru counter (19,700 on 2026-10-22) is one of the two. So the brief's "more than 20,000" is supported.
- Source concentration: Meduza is the only source for 4 of 8 claims and 9 of 18 events, and the URL is a mirror
  domain (`plugin-frontend.meduza.io`). Meduza is designated an undesirable organisation in Russia; a report for a
  Moscow developer should not cite it. Other outlets cover the same events: Афиша Daily, Т—Ж, The Blueprint, m24,
  msk1, Москвич Mag, Рамблер (citing Архи.ру), Reuters (citing ТАСС). F6.
- Facts the report must not blur: protection removed in 2025 (no building with protected status found); demolition
  under way since July 2026; ГЗК decision text not public, and reports disagree on full vs partial demolition. These
  bound what the image concept may claim (AGENTS R10).
- For T08 (not T04 fixes): Etalon statements in Афиша Daily and Т—Ж (incl. "no pseudo-historic replica" for parts that
  cannot be kept), m24 2026-07-17 (multifunctional cluster), the technopark announcement (investfuture.ru), the
  earlier "Форт" concept; check whether electrozavod-etalon.ru is an official Etalon site.
- For T03: the criticism framing in The Blueprint, Т—Ж, Афиша Daily; the 2026-07-24 detention of a lone picketer
  reported by Reuters (unverified by Reuters itself) is a risk signal for the negative-agenda section.

## Verdict: fix

## Fix list (numbered, atomic; R2 touches only these)
- F1 C03 → `confirmed`. Source: Reuters 2026-07-31 via https://english.aawsat.com/culture/5301950-thousands-support-campaign-save-soviet-industrial-%E2%80%98castle%E2%80%99-moscow
  ("Two petitions ... together collected over 21,000 signatures"). Keep 19,700 as the archi.ru count in the note.
  Update the 2026-07-31 timeline event and HANDOFF salient event 4. Fixed when C03 status, note and both mentions agree.
- F2 C04 note and the 2025-07 row: the number of de-listed objects differs by source (Meduza "более полутора тысяч";
  Москвич Mag 2026-07-08 "1322 объекта", https://moskvichmag.ru/?p=510124). Show both with sources; do not pick one.
- F3 2026-07-08 row: name the court as the source does ("Второй кассационный суд общей юрисдикции", Москвич Mag
  2026-07-08) and add that URL. Fixed when court name and source match.
- F4 2026-07-27 row: the cited source says "градозащитники", not «Архнадзор». Change the actor, or cite a source
  opened this session that names Архнадзор as the party appealing to the Supreme Court.
- F5 2026-06 ГЗК row: show the disagreement. Рамблер 2026-06-22 citing Архи.ру: "полный снос комплекса";
  Meduza: snos "с последующим «воссозданием»"; Etalon: no full demolition. Set confidence to `low` (decision text not public).
- F6 Every claim/event whose only source is Meduza: add a non-Meduza source opened this session as `source_url`
  where one exists, and move the Meduza link to `note` with the canonical domain `meduza.io`. Where none exists,
  keep Meduza and write "only source: Meduza" in `note`. Includes the Borodin row (Meduza dates it via Газета.ru;
  cite Газета.ru directly if it opens). Fixed when a script count of rows with a Meduza `source_url` matches the
  "only source" notes.
- F7 Petition addressee: the 2026-06-25 row says "мэру Москвы", the 2026-06-26 row "Путину и Собянину" (Активатика,
  linking to the same archi.ru page). State in both rows that sources differ on the addressee.
