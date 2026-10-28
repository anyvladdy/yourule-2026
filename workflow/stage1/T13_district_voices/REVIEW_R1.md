# REVIEW R1 — T13 district newspapers and residents' chats

Reviewer: Claude (facts and content). Date: 2026-10-28.

## Facts and format
- `out/newspapers.csv`: 4 rows; `out/chats.csv`: 3 rows; columns as in the card.
- Checked against the source, opened 2026-10-28:
  - Яблоко, statement of the Moscow bureau, 18.06.2026: demands disclosure of the project, an assessment of the complex's
    value regardless of formal status, an independent technical examination, open decisions; signed by К. Гончаров.
    Confirmed. The page also names the bureaus Nowadays and Syntaxis; not needed in the row.
  - КПРФ weekly summary, 03.08.2026: Д. Л. Медведев, КПРФ candidate for the State Duma (204th constituency), met voters
    at Электрозаводская ул., 12А. Confirmed.
- «Правда Москвы» №25: the article itself was not read (PDF). Its `position` is `inference`; it must not be used as
  evidence of what the article says.

## Content
- No district or municipal newspaper covered the site in June–October 2026 (search results recorded). This is a finding:
  the local press of the districts stayed silent, and party politics carried the topic (КПРФ, Яблоко) during the
  State Duma campaign. We use it in the audience map as `fact` (what was found) plus `inference` (why).
- Two of the three channels are new sources for Telegram collection: `sosedi_preobrazhenskoe` and
  `sokolinaya_gora_vao`. `act_preobrajenka` is already collected.
- VK stopped at a login wall, as D-21 requires. VK collection with the user's login stays open.

## Verdict: accept
Integration: the two new channels go to the Telegram collector run; party positions go to `docs/audiences.md`
(officials and deputies, preservationists) with these sources.
