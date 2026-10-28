# HANDOFF T17 — R1 — dsh — 2026-10-28

**Done:** `build_dzen.py` (`--help`; one command from the repo root rebuilds everything from the two raw files); `data/processed/corpus_dzen.parquet` — 1009 rows: 22 posts, 349 comments, 638 replies; `out/corpus_summary_dzen.csv` — 10 rows; `out/coverage_dzen.csv` — one row, 10 v2 columns plus `p3_largest_item_share` (52.84%) and `p3_top3_items_share` (93.20%); `out/build_checks.txt` — 19 checks PASS, parquet sha256 `4678cc49…`.

**Self-check:**
- [x] A1 one command; a second run gives the same parquet sha256.
- [x] A2 schema equal to `corpus_v2.parquet`; `pandas.concat` returns 15 349 rows.
- [x] A3 22 items and 987 comments in; dropped rows: none; every raw id appears once in the output.
- [x] A4 56 addressee prefixes replaced (14 distinct, none printed); two further rows changed by `mask()`: a business phone pair and a long numeric id inside an ok.ru URL. `out/` and this file hold no texts.
- [x] A5 T16 HANDOFF now reads «[name], …».

**Deviations:**
- `author_type`: item `media` → `org` (v2 vocabulary, `source_kind` keeps `media`); comment `channel` → `unknown`, because the raw has no display name and a channel is not necessarily an organisation.
- `is_source_owner` null everywhere: the raw has no per-comment owner flag; no comment hash equals its item hash, but 19 of 22 items carry no author hash.
- Addressee masking also covers Latin nicknames and emoji-wrapped display names (privacy). Common openers and place or object words (Да, Нет, ЖК, Метро, Каланчевка) are left alone.
- `source_id` null for the 2 items with unknown author and no publisher hash; `reposts` and `comments_count` null on comment rows.

**Unsure:** 1 comment has no date («14 ч») → `date_precision=unknown`, outside P3; the largest thread holds 521 of 524 comments the page loaded (raw limit, not a processing loss); 17 media and 2 unknown items have no author hash, so `unique_authors` counts 440 hashes.

**For R2 only:** —
