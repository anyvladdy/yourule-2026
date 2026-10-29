# Corpus manifest

Reader: people and agents. Goal: what the collected corpus contains, how it was selected and what it cannot show.
Every share in the analysis must name the slice of this manifest it comes from. Updated 2026-10-28 (Claude).

## Scope

- Cut date: 2026-10-28. Nothing published after collection is in the corpus.
- Analysis window for shares: 2026-06-01 → 2026-10-28 (the leak and the conflict). Earlier items are kept as background
  and reported separately by period (D-29): P0 before the fire of 2025-02-08; P1 2025-02-08 – 2025-09-14;
  P2 2025-09-15 – 2026-05-31; P3 2026-06-01 – 2026-10-28. Telegram starts at 2025-01-01 (files `*_early.jsonl` cover January–August 2025, D-31); Dzen at 2025-01-01; YouTube videos at
  2025-01-01; VK posts of all dates, VK comments only under posts from 2025-09-01.
- Unit of analysis: one post or one comment. Authors are counted separately from messages.
- People in the corpus are "participants of public discussion". Living in the district is not established for anyone,
  so no slice is called "residents" (Codex review P10).

## YouTube (official Data API, `src/collectors/youtube_comments.py`)

| Item | Value |
|---|---|
| Runs | 2026-10-28, `data/raw/youtube/2026-10-28/_run.json` (search ×3 runs, comments ×3 runs incl. pilot) |
| Queries | Электрозавод снос; Электрозавод Эталон; Электрозавод редевелопмент; сохранить Электрозавод; Электрозавод; Электрозавод Москва; Система Сити Эталон. One page of 50 per query, published on or after 2025-01-01 |
| Videos found | 171 unique; all saved with metadata, including those with 0 comments |
| Inclusion rule | "Электрозавод" in any case form (regex `электрозавод(?!ск)`) in title or description: 101 videos; 20 of them have no comments |
| Comments | 80 videos, 7,210 top-level comments and 3,716 replies (10,926). All replies received: 0 missing against `totalReplyCount` |
| Comment dates | 2025-02-08 → 2026-10-28; 628 top-level comments are before 2026-06-01 |
| Excluded | Meduza podcast (R12; it also fails the inclusion rule). Videos without the word in title or description, among them 5 with ≥100 comments that are off topic by title (МКАД, Arknights, music, football, car wash) and one MoscowWalks digest «Шуховскую башню снесут…» (343 comments): check by hand whether its segment is about the site |
| Not collected | Video content and transcripts (D-19, D-22) |

Known skew: one general news digest (varlamov, «Чё Происходит #331») holds 2,320 of 7,210 top-level comments (32%).
Two more of the five largest comment sets are under videos that are not about the site. Processing rule:

- topical video: "Электрозавод" in the title. Keep all comments with their thread context.
- digest video: the word only in the description. Keep only threads whose top comment or replies mention the site,
  demolition, the developer or the project; the rest are `off_topic`.
- report YouTube shares with and without the largest video.

## Telegram (public pages without login, `src/collectors/telegram_web.py`)

| Item | Value |
|---|---|
| Channels | 11 public channels from T01, plus 2 district channels from T13 (sosedi_preobrazhenskoe, sokolinaya_gora_vao) |
| Method | channel search `t.me/s/<channel>?q=` for "Электрозавод" (Telegram matches all case forms; checked on the pilot) and "Система Сити"; comments from the public discussion widget |
| Window | posts on or after 2025-09-01 |
| Pilot | 2026-10-28: act_preobrajenka 24 posts, engineer_media 23 posts; comments opened under 3 posts |
| Full run | 2026-10-28, `data/raw/telegram/2026-10-28/_run.json`, no errors: 13 channels, 140 posts, 1,464 comments. Most comments: moskvichmag 553, archnadzor_official 266, engineer_media 215, mskved 190. Group_etalon: 8 posts, 0 comments |
| Early run | 2026-10-28, January–August 2025 (`*_early.jsonl`): 36 posts in 8 channels, 35 after the fire of 2025-02-08; 76 comments (D-31) |
| Not covered | closed chats and groups (need login); reactions |

## VK (Selenium in Brave incognito with the user's manual login, `src/collectors/vk_web.py`)

| Item | Value |
|---|---|
| Runs | 2026-10-28, `data/raw/vk/2026-10-28/_run.json`: pilot, run 1, run v2 |
| Method | global post search «Электрозавод» (relevance order, loads 20 per page at the bottom); post search inside communities (search button on the community page); comments under posts that mention the site, published on or after 2025-09-01 |
| Communities searched | sokgor, club230930257 (T13); best_vao, vao_officiall, vao_moscow, vaonews, vostochnyiokrug, podsluh_preobr (run v2). vao_officiall and vostochnyiokrug returned no posts |
| Result (deduplicated by id) | 303 posts, 297 mention the site; 92 from 2025-09-01, 75 from 2026-06-01. 1,360 comments, 1,163 from 2026-06-01, 698 distinct authors (hashes). Comments mostly under best_vao (832), global search (259), vao_moscow (252) |
| Stopped | run v2 was stopped by hand at 13:43 UTC after the user was logged out of VK on another device (D-26). Not searched: prebr, janjilui, podsluh_lef, club180407106, club177781605, nine city-wide communities, Etalon's VK community |
| Privacy | people only as salted hashes; mentions of people in texts replaced with `[user]`; communities keep their names |

## Processed corpus (T11 v2, `data/processed/corpus_v2.parquet`, not in git)

| Item | Value |
|---|---|
| Rows | 14,340: YouTube 10,961 (100 videos, 7,204 top-level comments, 3,657 replies); Telegram 1,716 (176 posts, 1,540 comments); VK 1,663 (303 posts, 1,360 comments) |
| YouTube against raw | one video left out (only the plural «Электрозаводы»: 3 + 2 messages); 3 top-level comments and 57 replies were repeated snapshots and are removed by id |
| Analysis slice | reactions (comments and replies) in P3 that are relevant and have full context: 4,919 = YouTube 2,418, Telegram 1,338, VK 1,163. Left out: 522 YouTube messages in digest threads without a site mention, 17 Telegram messages without a parent |
| Context gaps | 8 Telegram replies whose parent is not in raw (18 rows with descendants), flagged `context_complete=false` |
| VK dates | 454 rows have a calendar date only (`date_precision=day`, `published_at` empty) |
| Concentration | the largest publication holds 715 of 2,418 YouTube, 365 of 1,338 Telegram and 359 of 1,163 VK reactions |
| Scripts and checks | `workflow/stage1/T11_processing/v2/` (build, NLP, tests, `out/build_checks.txt`); review `REVIEW_R1.md` |

## Dzen (T16 collection, T17 processing; `data/processed/corpus_dzen.parquet`, not in git)

| Item | Value |
|---|---|
| Collection | Dzen search «Электрозавод» in headless Brave without login, reader pace; stopped three times by SmartCaptcha (T16, D-33). Set: `data/raw/dzen/2026-10-28/` |
| Rows | 1,009: 22 items (20 articles, 2 videos), 349 comments, 638 replies; all items from June 2026 on, so Dzen does not test H8 |
| Analysis slice | 986 reactions in P3; one item holds 52.8% of them, three items 93.2% |
| Dates | calendar days only (`date_precision=day`); comment years inferred from the collection date; one comment without a date |
| Privacy | authors as salted hashes; addressee names at the start of replies replaced with `[user]` (56 rows) |

## Still to add

District party newspapers and statements (T13, read by hand), tenants and deputies (T14), Dzen (T16, if the pilot finds
material), the 27 media articles from T03 after relabelling (T15). Each gets a section here before its numbers are used.

## Archi.ru open letter signatures (D-42, D-43; `src/collectors/archi_petition.py`)

| Item | Value |
|---|---|
| Run | 2026-10-29, `data/raw/petitions/2026-10-29/archi_signatures.jsonl` and `_run.json`: 99 pages, no block, no errors |
| Content | 19,752 signatures, numbers 1–19,752 without gaps; 25.06–28.10.2026 (Moscow time) |
| Kept | number, self-described occupation (79% filled), time, comment (4,017). Names dropped while parsing, never stored |
| Snapshot | P01 19,752, P02 change.org 3,682, P03 «Яблоко» no counter (user, 2026-10-29, `snapshot.csv`) |
| Limits | a signature is not a person; occupation is optional and unchecked; only opponents sign |
| Outputs | `reports/tables/petition_occupations.csv`, `petition_occupation_top.csv`, `petition_daily.csv`, `daily_timeline.csv`, `signature_peaks.csv` |
