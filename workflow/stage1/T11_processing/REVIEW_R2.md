# REVIEW R2 — T11 fixes C1 and C3

Reviewer: Claude. Date: 2026-10-28.

- C1 fixed. The theme «Снос и утрата» is added: 21.1% of YouTube, 12.3% of Telegram, 19.3% of VK reactions
  (n = 2,418 / 1,338 / 1,163, 1 Jun – 28 Oct 2026). Slide 02 and `ANALYSIS.md` no longer rank themes; «лидирует» is gone.
- C3 fixed. N-grams count one vote per platform account (1,775 accounts, 35 messages without an author left out); the
  bigrams of the repeated messages are gone from the top of `ngrams.csv`.
- `test_nlp_r2.py` (4 tests) and `test_v2.py` (5 tests) pass, rerun by the reviewer. Corpus sha256 unchanged.
- Known limit, no fix needed: the demolition dictionary catches «ломать» but not «ломают» or «сломали»; its share is a
  lower bound. Theme shares stay descriptive (D-32).

## Verdict: accept
