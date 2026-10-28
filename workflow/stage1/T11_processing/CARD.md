# T11 — Processing: YouTube and Telegram raw data into one corpus table

Reader: worker agent. Human summary of this stage: `workflow/stage1/README.md`.

- **Stage:** 1–2 (cut, D-19) · **Worker:** Codex · **Content review:** Claude · **Fallback:** Claude
- **Time box:** 90 min · No web access. This card requires a processing script (R6); it collects nothing new.

## Goal
One deduplicated, pseudonymised table of videos, posts and comments with relevance and window flags.
Labelling (shared codebook, 50/25/25 split) and all stage-3 counts will run from this table.

## Inputs (read only these)
- `AGENTS.md` §0; §3 "Common record schema"; §5
- `docs/data_cards/corpus_manifest.md`: selection rules, topical vs digest videos, analysis window
- `data/raw/youtube/2026-10-28/`: `videos_*.jsonl`, `comments_*.jsonl`. Skip files with `_pilot` or `_partial` in the name.
- `data/raw/telegram/<latest date>/`: `posts_*.jsonl`, `comments_*.jsonl`. Skip `_pilot` files. The full Telegram
  run may still be going: process what exists; the script must rerun cleanly when more files arrive.
- `workflow/stage0/T01_telegram_video/out/telegram.csv`: column `owner_type` per channel
- `workflow/stage0/T06_keyword_variants/out/variants.yaml`: `case_forms` of «Электрозавод»
- `.secrets/hash_salt`: salt for author hashes. Read it in the script; never print or copy it.

## Method
1. Write `build_corpus.py` in this card folder, with `--help`. Run from the repo root:
   `.venv/bin/python workflow/stage1/T11_processing/build_corpus.py`.
   You may install `pandas` and `pyarrow` with `uv pip install --python .venv/bin/python <pkg>==<version>`;
   list the versions in HANDOFF (Claude adds them to `pyproject.toml`).
2. YouTube rows: one per included video (`row_type=video`, text = title + description), one per top-level comment
   (`comment`), one per reply (`reply`). `source_id` = video id; `thread_id` = top-level comment id;
   `parent_id` = video id for top-level comments, top-level comment id for replies.
   Included videos = the manifest rule (regex in title or description), deduplicated across all `videos_*.jsonl`.
3. Telegram rows: one per post (`post`) and per comment (`comment`). `source_id` = channel; `thread_id` = post id;
   `parent_id` = the replied comment if any, else the post.
4. Pseudonymise. `author_id_hash` = first 16 hex of sha256(salt + platform + ':' + raw author id); the YouTube raw id is
   `authorChannelId.value`. Telegram comments already carry `sender_hash`: keep it. No commenter names, handles,
   channel ids or avatar URLs in the output. In `text`, replace @handles, e-mails and phone numbers with `[user]`,
   `[email]`, `[phone]`. `author_display` only for video channels and Telegram channels (media, organisations, public
   bloggers). A YouTube comment written by the video's own channel gets `is_source_owner = true`.
5. Flags:
   - `source_kind`: YouTube `topical` (site regex matches the title) or `digest` (description only);
     Telegram = `owner_type` from T01.
   - `relevant` + `relevance_reason`:
     YouTube topical video → all its rows true, `topical_source`.
     YouTube digest video → a thread is true if any message in it matches the site regex or a topic stem,
     `thread_mentions`; otherwise false, `off_topic_digest`. The video row itself is true, `digest_source`.
     Telegram post → true if the site regex matches its text, `post_mentions`; else false, `search_hit_without_term`.
     Telegram comment → same value as its post, `thread_context`.
   - `in_window`: `published_at` from 2026-06-01T00:00:00Z to 2026-10-28T23:59:59Z.
   - `lang`: `ru` if at least half of the letters are Cyrillic, `other` otherwise, `empty` if there are no letters.
   Site regex: built from the `case_forms` of «Электрозавод», case-insensitive; it must not match
   «Электрозаводская», «Электрозаводской», «Электрозаводск». Topic stems (case-insensitive, word start):
   `снос`, `снес`, `демонтаж`, `эталон`, `фасад`, `наслед`, `памятник`, `башн`, `шухов`, `завод`.
6. Deduplicate by (`platform`, `id`); count what was removed.
7. Self-tests in the script; exit non-zero on any failure: unique (`platform`, `id`); every `parent_id` exists in the
   table; YouTube top-level + reply rows equal the raw totals of the included comment files; no raw
   `authorDisplayName` or `authorChannelId` value appears anywhere in the output; every `published_at` is UTC ISO 8601.

## Output
- `build_corpus.py`
- `data/processed/corpus.parquet` (not in git, D-24). Columns: the common record schema from AGENTS §3, plus
  `platform`, `row_type`, `source_id`, `source_kind`, `is_source_owner`, `relevant`, `relevance_reason`, `in_window`.
  A field the platform does not give is null, never 0.
- `out/corpus_summary.csv`: row counts by `platform` × `source_kind` × `row_type` × `relevant` × `in_window`, and unique
  authors per platform. No texts. This file goes into git.
- `out/test_report.txt`: the script's output from the last run.
- `HANDOFF.md` per `workflow/templates/HANDOFF.md`.

## Acceptance criteria
- [ ] A1 one command rebuilds the parquet and the summary from raw; a second run gives identical counts
- [ ] A2 all self-tests pass; `test_report.txt` matches a fresh run
- [ ] A3 YouTube comment and reply rows match raw (at card writing: 7,210 top-level comments and 3,716 replies in 80 files)
- [ ] A4 no commenter names, handles, channel ids or avatar URLs in the parquet, summary, report or HANDOFF;
      @handles, e-mails and phones masked in `text`
- [ ] A5 relevance follows Method 5 exactly; the summary gives counts per `relevance_reason`
- [ ] A6 HANDOFF lists installed packages, dropped rows with reasons, and raw fields the schema could not hold

## Rules quoted for this card
- Write only inside `workflow/stage1/T11_processing/`, plus `data/processed/corpus.parquet`, plus your BOARD row.
  Do not edit raw data (R7), `config/`, `docs/` or `src/`.
- Do not paste comment texts or author fields into HANDOFF or chat; at most 3 short masked examples.
- R5: public content only; private individuals only as hashes or roles.
