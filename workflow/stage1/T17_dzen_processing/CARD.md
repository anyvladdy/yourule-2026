# T17 — Dzen: raw items and comments into the corpus schema

Reader: worker agent. Human summary of this stage: `workflow/stage1/README.md`.

- **Stage:** 1–2 · **Worker:** dsh · **Content review:** Claude · **Fallback:** Claude
- **Time box:** 60 min · No web access. This card requires a processing script (R6); it collects nothing.

## Goal
Dzen rows in exactly the schema of `data/processed/corpus_v2.parquet` (T11 v2, Codex), so that labelling (D-28) and the
stage-3 counts read Dzen together with YouTube, Telegram and VK.

## Inputs (read only these)
- `AGENTS.md` §0
- `workflow/stage1/T11_processing/v2/build_corpus_v2.py` and `workflow/stage1/T11_processing/build_corpus.py`: the
  T11 pipeline. Import from them with `importlib`, as `build_corpus_v2.py` imports the base; do not edit them. Use
  `SCHEMA`, `period()`, `mask()`, `language()`, `make_site()`, `TOPIC`.
- `workflow/stage1/T11_processing/REVIEW_R1.md`, `workflow/stage1/T16_dzen/REVIEW_R1.md`
- `data/raw/dzen/2026-10-28/items.jsonl`, `comments.jsonl`. Only this folder: the two earlier folders hold the same
  articles, and the pilot comments keep addressee names.

## Method
1. Write `build_dzen.py` in this card folder, with `--help`. Run from the repo root:
   `.venv/bin/python workflow/stage1/T17_dzen_processing/build_dzen.py`.
2. Rows: one per item (`row_type=post`), one per comment (`comment` at depth 0, `reply` at depth 1);
   `platform` = `source` = `dzen`; `id` = raw id; `thread_id` = item id. `parent_id` = item id for depth 0; for depth 1
   the id of the root comment it answers (raw `parent_id` is the root's number: `<item>-root<N>`; check this on the raw
   before relying on it). Item `text` = title + newline + text. `source_id` = the item's `author_display` for media
   and organisations, else its `publisher_url_hash`; `source_kind` = the item's `author_type`.
3. Dates: raw dates are calendar days, so `published_at` = null, `published_date` = the day, `date_precision` = `day`,
   as VK in v2. A row without a date: `published_date` null, `date_precision` `unknown`. `in_window` and `period` from
   `published_date` with v2's `period()`.
4. Authors and masking: keep the raw `author_id_hash`; `author_display` only for media and organisation channels.
   Pass every text through `mask()`. Also replace an addressee name at the start of a reply («Имя,» or «Имя Ф.,») with
   `[user],`; only depth-1 rows, only a capitalised word followed by a comma that is not a common Russian word
   (check a list such as Да, Нет, Ну, Жаль, Вот, Так). Report in HANDOFF how many were replaced, never the names.
5. Relevance as in v2: item `relevant` if the site regex matches its text, reason `post_mentions`, else
   `search_hit_without_term`; comments inherit, reason `thread_context`. `matched_keywords` as in v2.
6. Counters: `likes`, `comments_count` as integers or null; `views` null. `collector_version` = `t17_dzen/1.0`.
7. Self-tests; exit non-zero on any failure: column names, order and types equal the schema of
   `data/processed/corpus_v2.parquet`; `pandas.concat` with it works; ids unique; every `parent_id` and `thread_id`
   exists; no `day` row has `published_at`; no unmasked handle, e-mail or phone; no addressee pattern left at the start
   of a reply; input sha256 unchanged after the run.

## Output
- `build_dzen.py`
- `data/processed/corpus_dzen.parquet` (not in git, D-24)
- `out/corpus_summary_dzen.csv`: the columns of `T11_processing/v2/out/corpus_summary_v2.csv`. No texts.
- `out/coverage_dzen.csv`: the columns of `T11_processing/v2/out/coverage.csv`, plus the share of reactions in P3 under
  the largest item and under the three largest.
- `out/build_checks.txt`: the script's output from the last run.
- `HANDOFF.md` per `workflow/templates/HANDOFF.md`.

## Acceptance criteria
- [ ] A1 one command rebuilds the parquet and the summaries from raw; a second run gives the same sha256
- [ ] A2 schema equal to corpus_v2; the concat test passes
- [ ] A3 22 items and 987 comments in, every dropped row listed with its reason
- [ ] A4 no names of private people in any output, addressees included; no comment texts in `out/` or HANDOFF
- [ ] A5 T16 HANDOFF self-check A2: the quoted addressee name replaced with `[name]`

## Rules quoted for this card
- Write only inside `workflow/stage1/T17_dzen_processing/`, plus `data/processed/corpus_dzen.parquet`, plus your BOARD
  row, plus the one fix in `workflow/stage1/T16_dzen/HANDOFF.md` (A5).
- Do not edit raw data (R7), the T11 files, `config/`, `docs/`, `src/`. No NLP here: Claude adds Dzen to labelling.
- R5: public content only; private individuals only as hashes or roles.
