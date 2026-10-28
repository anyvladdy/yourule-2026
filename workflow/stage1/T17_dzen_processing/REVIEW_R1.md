# REVIEW R1 — T17 Dzen processing

Reviewer: Claude. Date: 2026-10-28.

## Checked (reviewer's own read-only checks on `data/processed/corpus_dzen.parquet`)
- Schema equal to `corpus_v2.parquet` (names, order, types). 1,009 rows: 22 posts, 349 comments, 638 replies; ids
  unique; every `parent_id` and `thread_id` exists.
- `author_display` only on organisation rows; no `day` row has `published_at`; 1,008 rows in P3, one without a date.
- Replies that still start with a capitalised word and a comma: 11, all common words or forms of address (Да, Нет,
  Давайте, Метро…), no names.
- `out/` and HANDOFF hold counts only. T16 HANDOFF A5 fixed.

## Content
Dzen adds 986 reactions in P3. One item holds 52.8% of them and three items hold 93.2%: Dzen shares are reported with
and without the largest thread.

## Verdict: accept
Dzen joins labelling as a separate addition to the drawn sample (the YouTube, Telegram and VK sample stays as drawn,
D-34).
