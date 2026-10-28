# Etalon's own channels: what the company said about Электрозавод and where

Reader: people and agents. Goal: evidence for the message gap (what Etalon said vs what audiences heard; report
sections 3 and 4). All sources opened 2026-10-28. Collected by Claude (BOARD row "Etalon's own channels", D-25, D-26).

## Findings

1. `fact` During the conflict (2026-06-01 → 2026-10-28) Etalon published nothing about Электрозавод or the «Форт»
   project in its own channels checked here. It kept publishing on other topics: about 40 Dzen publications in
   four months (market analytics, kindergartens, sustainability report, a change of company president) and 17 website
   news items since March. The Telegram channel published nothing at all after 2026-05-31.
2. `fact` The company's statements in that period reached the public only through media: the eight statements S01–S08
   in `docs/project_facts/developer_statements.csv` come from m24.ru (5), afisha, mskagency and RBC.
3. `fact` Comments are closed under all Etalon Telegram posts collected (8 posts, discussion widget not available), so
   reactions to the company's messages happen in other people's channels and groups.
4. `inference` The audience heard the company mostly as quotes inside critical or neutral news. A short quote such as
   "сохранит входную группу и фасады" travels without the context of the project. This fits the brief's statement that
   critics read it as confirmation of demolition; whether it caused that reading is not shown by these data.

## Evidence

| Channel | What was checked | Result | Source |
|---|---|---|---|
| Telegram @Group_etalon | Channel search for «Электрозавод», «Электрозаводе», «Система Сити», «Форт», posts from 2025-09-01 | 3 posts about the site: 2025-09-15 (reconstruction announced), 2025-10-23 (Архитектон nominations), 2026-05-08 (project «Форт»). None from 2026-06-01. Comments closed | https://t.me/s/Group_etalon ; raw `data/raw/telegram/2026-10-28/posts_Group_etalon*.jsonl` |
| Telegram @Group_etalon, whole feed | Every post from 2026-06-01 (feed read without a search word) | No posts at all; the newest post is 2026-05-31 (construction progress, «Шагал») | https://t.me/s/Group_etalon ; raw `posts_Group_etalon_all.jsonl` |
| Dzen dzen.ru/gk_etalon | Channel page read in Brave incognito, scrolled about four months back | About 40 publications, newest "5 days ago": market analytics, kindergartens, ESG report, ratings, the handover from president Юрий Бородин to Тонко Санкович (to verify before use). None mention Электрозавод, «Форт», facades or heritage | https://dzen.ru/gk_etalon ; raw `data/raw/etalon/2026-10-28/dzen_gk_etalon_lines.json` |
| MAX max.ru/id7717154511_biz | Channel page | Posts are not visible without the MAX app or login; not checked | https://max.ru/id7717154511_biz |
| Website, Moscow news | All news items shown after pressing "Показать еще" back to March 2026 | 17 items, 26.03.2026–14.10.2026; none mention Электрозавод, «Форт», facades or heritage. The 11.06.2026 "non-core asset" sale is a 1 ha plot on Lobachevsky Street (project «Крылья») | https://etalongroup.ru/msk/news/ ; https://etalongroup.ru/msk/news/gruppa-etalon-realizovala-neprofilnyy-aktiv-v-moskve/ |
| Website, project list | Projects on the main page | No page for «Форт» or Электрозавод (listed: Шагал, Воксхолл, Мариин Парк, Соколин Парк, Нагатино Ай-Лэнд, Десятка, Изумрудные Холмы) | https://etalongroup.ru/ |
| YouTube | 171 videos found by the YouTube collector | No video from an Etalon channel | `docs/data_cards/corpus_manifest.md` |
| VK community | Not collected | Stopped with the VK collection (D-26) | — |
| Press | T08 developer statements | 8 statements, 2025-07-15 → 2026-09-30, all through media | `docs/project_facts/developer_statements.csv` |

## Limits

- The website check covers the Moscow news section only, back to 26.03.2026; investor releases were not checked.
- MAX and Rutube channels were not checked; VK community not collected (D-26). The site lists all five channels.
- Dzen dates are relative ("4 месяца назад"); the window is approximate.
- Telegram search on `t.me/s` finds word forms; a post that names the site only in an image would be missed.
- Silence in owned channels is a fact about these channels, not about all company communication (letters, meetings,
  replies to journalists are not visible here).
