# HANDOFF T16 — R1 — dsh — 2026-10-28

**Done:** `collect_dzen.py` (Brave headless + `--incognito`, throwaway profile deleted at exit, 2–5 s between pages, stops on a captcha, no scheduled restarts). Raw: `data/raw/dzen/2026-10-28/` (22 items, 987 comments, `_run.json`); `2026-10-28-run1-pilot/` (10 items, 778 comments, first pilot with broken comment dates and addressees); `2026-10-28-run2-partial/` (4 items, 16 comments, stopped by the worker). `out/run_summary.csv` — 6 runs, captcha stops as `captcha`.

**Final set:** all three folders stay in `data/raw/dzen/`. Unique items by url: 22 (the 14 items of the two earlier runs are the same articles). Comments: 987 in the final folder; 1474 rows survive exact dedupe across folders, but 487 are the pilot copies of the same comments with the addressee's name left in — they add nothing.

**Periods (D-29)**, items by publication date, comments by their own date:
- до 2025-02-08: 0 items, 0 comments
- 2025-02-08…2025-09-14: 0, 0
- 2025-09-15…2026-05-31: 0, 0
- с 2026-06-01: 22 items, 987 comments
13 search rows older than 2025-01-01 were counted and not opened in each full run.

**Pilot decision:** 10 of 10 pilot items after 2025-09-01, comments readable without login → full run.

**Self-check:** A1 [x] three runs ended on SmartCaptcha, nothing bypassed; A2 [x] authors only as salted hashes, @mentions masked (6 comments still start with a plain-text addressee name, e.g. «[name], …» — strip in processing); A3 [x] pilot rule applied; A4 [x] item dates from the page, comment dates from labels with the year inferred and noted; A5 [x] `out/` holds counts and 3 masked examples only.

**Deviations:** video pages show no date → search card label used and noted (2 of 22 items); no per-comment anchor → ids are positional, `url` null; platform-hidden comments counted, not opened; the 2025-01-01 pass stopped at 22 items — 20 came before the 19:01 captcha, the resume added 2 June items before the pace fell to 5 min per item and the worker stopped it. Periods before 2026-06 are empty: Dzen does not test H8.

**Captcha stops** (local): 18:15:58 search, 19:01:29 item, 19:14:40 search. 18:29 run died with the browser tab, no captcha. No runs after 19:58.

**Why `.tmp`:** the first two run folders were moved out of `data/raw/dzen/` to `.tmp/` to restart cleanly; R7 forbids that. Both were copied back unchanged (sha256 identical) as `2026-10-28-run1-pilot` and `2026-10-28-run2-partial`; nothing was deleted.

**Unsure:** 23 comments are cut at the platform «ещё» clamp; 1 comment has no date («14 ч»); the hot thread loaded 521 of 524 comments; comment order is «Сначала популярные».

**3 masked examples** (author hashes only):
- «Невероятно жаль, если останется только фасад» (21 likes, 2026-10-14).
- «От Серпа и Молота осталась только станция, от Электрозавода останется станция метро» (395 likes, 2026-09-07).
- «Дай бог, если застройщик сохранит этот великолепный комплекс промышленной архитектуры» (1 like, 2026-09-30).
