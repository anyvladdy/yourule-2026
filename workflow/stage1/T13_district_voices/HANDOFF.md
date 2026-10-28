# HANDOFF T13 — R1 — dsh — 2026-10-28

**Done:**
- `out/newspapers.csv` — 4 rows: «Правда» №60 (09.06.2026), «Правда Москвы» №25 (07.07.2026), сводка МГК КПРФ (03.08.2026), заявление московского «Яблока» (18.06.2026).
- `out/chats.csv` — 3 rows: «СОСЕДИ Преображенское» (640), «Активная Преображенка» (2.74K), «Реальные Соколинцы» (8.12K).

**Self-check** (copy from CARD, tick honestly; explain any unticked):
- [x] A1 Site is in Преображенское: boundary runs along ул. Электрозаводская — Закон Москвы №13-47, ст. 4, https://base.garant.ru/309690/1b93c134b90c6071b4dc3f495464b753/ . Adjacent districts (Соколиная Гора, Богородское, Басманный across the Yauza) are inferred from the same boundary text — `inference`.
- [x] A2 Every URL was opened this session; member counts are copied as displayed (640 / 2.74K / 8.12K) with the date seen.
- [x] A3 Each newspaper row is about the plant itself. «Правда» and «Яблоко» texts read in full; «Правда Москвы» only through the issue summary on the МГК site; dates are from the pages (МГК date from the URL).
- [x] A4 No private individuals; only public figures, parties, organisations (Костриков, Гончаров, Медведев).
- [x] A5 Nothing found for municipality and prefecture types; queries and results in "Unsure".
- [x] A6 No outlet designated undesirable in Russia was used.

**Deviations from the card:**
- Chat rows are public Telegram channels/communities with open comments, not group chats. No VK row: vk.com and m.vk.com returned a login wall/shell, so the run stopped there (D-21/D-23).
- «Правда» is the central party newspaper, not a district branch; kept because no district-branch print paper covered the site.

**Unsure / could not verify:**
- «Правда Москвы» №25: the article is inside a PDF; `web_fetch` cannot read PDF. Position is labelled `inference`.
- Telegram previews show post time, not date. `evidence_date` left empty and the note gives the content anchor; do not treat it as a publication date.
- District papers «Преображенка для вас», «Взгляд с Соколиной горы», «Восточный округ»: site search for «Электрозавод» and «снос» returned no June–October 2026 redevelopment coverage (only culture, traffic, asphalt plants). Queries: `?s=Электрозавод`, `?s=снос` on each site.
- No district/okrug party-branch print newspaper found. Queries: «газета Преображенское муниципальный округ», «КПРФ ВАО газета», «Правда Москвы Электрозавод 2026», «муниципальный вестник Преображенское pdf».
- VK groups not checked: search gave https://vk.com/sokgor and https://vk.com/club230930257, but both pages require login; no member counts.
