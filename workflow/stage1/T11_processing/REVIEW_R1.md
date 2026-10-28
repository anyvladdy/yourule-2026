# REVIEW R1 — T11 corpus v2 and first NLP pass

Reviewer: Claude (facts and content). Date: 2026-10-28.

## Checked
- `data/processed/corpus_v2.parquet`: 14,340 rows (YouTube 10,961; Telegram 1,716; VK 1,663). Telegram 176 posts and
  1,540 comments = full run 140 + 1,464 plus `_early` 36 + 76. VK 303 posts and 1,360 comments, as in the manifest.
- YouTube 7,204 top-level comments and 3,657 replies against 7,210 and 3,716 in the manifest: one video is dropped
  (only the plural «Электрозаводы»; 3 + 2 messages), and 3 + 57 repeated snapshots are removed by id. Explained.
- Privacy, read-only checks on the parquet: masks glued to a preceding letter occur once (an ad link); no `vk.com/id…`
  links; `author_display` is filled only for videos, channel posts, VK community posts and 8 community comments.
  57 `t.me` links and some community links remain in local texts; the parquet is not in git.
- Relevance: no `post_mentions` row matches only «Электрозаводск…»; `in_window` equals period P3 on every row.
- `v2/test_v2.py`: 5 tests OK, rerun by the reviewer. The build was not rerun by the reviewer because it rewrites
  Codex's outputs; `v2/out/verification.json` reports an identical repeat.
- `etalon_analysis_v2.zip` and `executive_brief.html` hold no comment texts and no author ids.

## Deviations from the card, accepted
- D1 Parent criterion: 8 Telegram replies have no parent in raw (18 rows with descendants). They are flagged
  `context_complete=false`, nothing is invented, and 17 are left out of the window slice.
- D2 Strict slice: YouTube digest threads that match only topic stems (522 messages) are left out of the analysis
  slice. This is stricter than the card and fits Codex review P10.

## Content issue, fix before use
- C1 The headline «Историческая ценность лидирует среди тем» (slide 02, first inference in `v2/ANALYSIS.md`) follows from
  the choice of dictionaries. None of the eight covers demolition. In the same slice, words снос / снес / уничтож /
  ломать / разруш occur in 19.8% of YouTube, 12.3% of Telegram and 19.3% of VK reactions, above the heritage dictionary
  (15.6 / 8.6 / 10.2%). Dictionaries of different breadth cannot be ranked against each other. Fix: add a theme
  «Снос и утрата» and drop the word «лидирует» and the ranking from the slide and the inference; keep per-theme shares
  as description. The ranking of criticism lines will come from the labelled sample (D-28).
- C2 NMF topic 1 (1,021 of 3,018 documents) is everyday talk without a subject; the report does not present it as a theme.
- C3 One Telegram author posted 12 near-identical messages under one moskvichmag post within 1.5 hours on 2026-07-09
  (10 distinct texts). They make about 15 of the top bigrams in `ngrams.csv` (count 10 each) and feed the word
  «коммунист» in topic 1. Exact-duplicate merging does not catch them. Fix: count n-grams once per author, or merge
  near-duplicates by author. The labelling sample will cap items per author.

## For stage 3
Weekly peaks of reactions: YouTube week of 29 Jun (784), Telegram 6 Jul (527), VK 22 Jun (428), YouTube 20 Jul (382)
and 28 Sep (279). Match them to the event timeline before naming triggers.

## Not in this version, by design
Stance and tone (next step, D-28); Dzen (after the T16 HANDOFF).

## Verdict: accept with fixes C1 and C3
C1 and C3 are short fixes for Codex and do not block labelling. Integration: `corpus_v2.parquet` is the base for
labelling (D-32); `.gitignore` keeps `out/*.parquet`, `out/*.zip` and the matplotlib cache out of git
(`nlp_annotations.parquet` holds comment ids that lead back to authors); `docs/data_cards/corpus_manifest.md` updated.
