# REVIEW T03 — R1

## Facts and format (dsh, standing in for Codex; D-16)
Sample checked: A01, A04, A14, A16, A19, A25 (6 of 27, stratified by viewpoint and outlet) plus
A07, A18, A22 opened as well (A22 carries the 21 000 figure; A07/A18 to test `syndicated_copies`).
Outlets in the sample: РБК Недвижимость, Афиша Daily, Москва 24, MSK1 (2 rows), Новая газета.
Viewpoints in the sample: developer 2, critical 2, balanced 1, other 1.

Opened 2026-10-22, HTTP 200: A01 (realty.rbc.ru; the direct page times out for this tool, read through
the r.jina.ai text proxy of the same URL), A04 daily.afisha.ru, A14 m24.ru, A16 and A25 msk1.ru (JS
shell on direct fetch, text read through the r.jina.ai proxy), A19 novayagazeta.ru (same), A22
english.aawsat.com, A07 and A18 moskvichmag.ru.

| Criterion | Pass? | Note |
|-----------|-------|------|
| A1 | yes | 27/27 rows carry `accessed` = 2026-10-22 and every sampled URL opens. A01's note («Открыт через amp-версию») no longer describes reality: `…/amp` returns 404, the canonical URL is live — same text. |
| A2 | partial | Title, date, outlet and `key_claim` match the article in all 8 rows I read, and `criticism_lines` match in 7 of 8. A16 carries two lines the article does not argue (F1); A25's lines are right but its note contradicts the page (F3). |
| A3 | yes | 16 outlets; pro-city/developer Москва 24 (A14, A26) and Вечерняя Москва (A21); critical Архи.ру (A03), Т—Ж (A11), Новая газета (A19), Афиша Daily (A04), Ведомости. Город (A15). |
| A4 | partial | No invented article, date or name in the sample; A10's afishadaily.ru entry is a real mirror (opened, same text). `syndicated_copies` is wrong on A07 and A18 (F2) and lists unopened URLs on A22 (F5). |
| A5 | yes | HANDOFF lists 6 queries and states the stop was the time box and the size cap, not the 5-search rule — a stop condition the card allows. |

Format: 12 columns per row, 27 rows, no repeated `art_id`, no duplicate URL, all `criticism_lines` labels are
from the card list (no `new:` labels). Counts recomputed from the file match HANDOFF exactly: 16 outlets;
critical 15 / developer 6 / balanced 5 / other 1; heritage_loss 21, facadism 9, loss_of_cultural_spaces 7,
commercial_density 6, no_masterplan_transparency 4, collusion_with_city 3, no_real_hearings 1,
local_impacts 0; dates 2025-07-15 → 2026-09-10. 27 ≤ 30 cap.

Rows checked field by field:
- A01 — 15 July 2025, 11:45; advertorial labelled «Реклама … erid:2SDnjcsnhFt»; the page does call the
  complex «объект культурного наследия федерального значения» and does give ~290k m² housing, 52k m²
  commercial, 250k m² technopark, kindergarten. Speaker list matches.
- A04 — 21 June, 09:45 (year not printed on the page; 2026 by context); ГЗК demolition approval with
  Архи.ру as source; Монич and Гершман quotes present; «Позиция «Эталона» не приведена» is true.
- A14 — 26 June 2026, 11:31; Etalon press service via ТАСС; «более 800 тыс. м²», «более 287 тыс. м²
  жилья» present.
- A16 — 2 July 2026, 10:14; the «согласованный мэром» wording is the KPLN bureau's own quote; Etalon
  declined to comment; towers, business centre, park, Яуза embankment are in the text.
- A19 — 8 July 2026, 11:59 UTC; Соседов, Чарахчьян and Самовер all quoted; «юридический трюк» present;
  the 2024 amendment and its contradiction with federal law is the article's own claim.
- A25 — 8 September 2026, 20:31; строение 10 demolished and строение 11 being dismantled — correct.
  The page also says «даже частичный снос фасада Электрозавода — большая потеря для Москвы» and runs
  the caption «сносят, несмотря на сопротивление москвичей».
- A18 — 8 July 2026; около 150 человек at the hearing; 1 322 objects — both correct.
- A22 — 31 July 2026, 09:10; «Two petitions … have together collected over 21,000 signatures» —
  confirms the figure T02's HANDOFF uses; «Reuters could not independently verify» the 24 July
  detention, as the note says.

Minor, not an item: A04 and A10 print no year on the page, A10's note says so and A04's does not.

## Content (Claude)
- Claude was the worker on this card, so the content check is limited; dsh's facts check is the independent part.
- Media framing is about heritage and authenticity: heritage_loss 20 of 27, facadism 9. Local impacts appear in 0 articles,
  so H3 (residents care about practical issues) has no media support; stage 3 tests it on district channels.
- Three items change the negative-agenda section: the 2025 RBC advertorial calling the site a federal heritage object (A01);
  the developer's own bureau calling the design "согласованный с мэром" (A16); developer news on city outlets carries no
  critics at all (A14, A21, A26), which the opponents can present as one-sided.
- Gaps: no Коммерсантъ or РБК news on the 2026 conflict; no television; critics' reference cases (Военторг, Детский мир) not covered.

## Verdict: accept (R2 fixes F1–F5 applied by the worker; counts recomputed by script)

## Fix list (numbered, atomic; R2 touches only these)
- F1 A16, `criticism_lines`: `heritage_loss` is not argued in the article (it reports renders, the
  bureau's «согласованный мэром» quote and Etalon's no-full-demolition statement), and
  `loss_of_cultural_spaces` is only implied by the former creative cluster. Keep `collusion_with_city`
  and `commercial_density`, drop or evidence the other two. Knock-on if dropped: heritage_loss 21 → 20,
  loss_of_cultural_spaces 7 → 6 in HANDOFF.
- F2 A07 and A18, `syndicated_copies`: `https://moskvichmag.ru/?p=506419` and `?p=510124` redirect to
  the same moskvichmag.ru article in the same row, they are not copies of it. Fixed when the field is
  empty or holds a different outlet's copy, as A10's afishadaily.ru entry does.
- F3 A25: the note «Фоторепортаж без оценок; линия heritage_loss по теме, не по тексту» contradicts the
  page, which contains an evaluative sentence («большая потеря для Москвы») and the caption «сносят,
  несмотря на сопротивление москвичей». Fixed when the note describes the page as it is and the
  `viewpoint` choice (`other`) is justified against that framing or changed.
- F4 A10 and A22, `quoted_actors`: named speakers from the page are missing. A10 also quotes Елизавета
  Лихачева, Айрат Багаутдинов and Дарья Радченко; A22 quotes Инна Крылова and «Архнадзор». Fixed when
  the field lists every named org/public figure the row's article quotes (roles, not private persons).
- F5 A22, `syndicated_copies`: theprint.in, kfgo.com and whbl.com are listed and, per the note, were
  never opened. Fixed when each listed URL has been opened or is removed.

## Escalation (R2 only): item → owner (Claude|Codex)
