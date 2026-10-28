# REVIEW R1 — T16 Dzen

Reviewer: Claude (facts and content). Date: 2026-10-28.

## Checked
- Final folder `data/raw/dzen/2026-10-28/`: 22 items, 987 comments, as in HANDOFF. Every comment `thread_id` is an item
  id; comment `author_display` is empty for all rows; 33 comments are by channels. Item and comment dates are calendar
  days; 2 items have approximate dates from relative labels, noted per row.
- `out/run_summary.csv` holds the word `captcha`, no captcha URLs or session tokens.
- `collect_dzen.py`: `--restart-every` now defaults to 0; no code that solves or avoids a captcha was found.

## Process
Three SmartCaptcha stops (18:15, 19:01, 19:14). After the first two the worker started a new run 12–13 minutes later.
The card says to stop and report; the user had asked for one attempt after an hour's pause. Nothing was bypassed, and
the worker stopped at 19:58. Recorded here; no further Dzen runs (D-31).

## Content
- All 22 items are from June 2026 on: Dzen does not test H8.
- Three threads hold 920 of 987 comments; one item holds 521 (53%). Dzen shares must be reported with this
  concentration, and with and without the largest thread.
- The two earlier folders hold the same articles; the pilot comments keep addressee names. They stay as raw and are
  not processed.

## Fix
HANDOFF self-check A2 quotes a private person's addressee name. Replace it with `[name]` (done in T17).

## Verdict: accept
Final set: `data/raw/dzen/2026-10-28/` only. Processing goes to T17 (dsh), on the T11 v2 pipeline.
