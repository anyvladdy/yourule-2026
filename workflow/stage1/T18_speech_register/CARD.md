# T18 — Speech register and self-disclosure: who is dissatisfied, as far as the texts can show

Reader: worker agent. Human summary of this stage: `workflow/stage1/README.md`.

- **Stage:** 3 · **Worker:** Codex · **Content review:** Claude · **Fallback:** Claude
- **Time box:** 2 h · Due 2026-10-30 12:00 Moscow time. No web access, no collection. This card requires a script (R6).

## Goal
The user asks: who is most dissatisfied with the redevelopment, younger or older people, or everyone alike? The
corpus has no age of authors. This card measures what the texts do show and tests whether that is enough:
(a) speech register: markers of youth internet slang and of an older or formal register; (b) self-disclosure: authors
who say their age, generation, that they live nearby, or that they or their family worked at the plant. Each is
crossed with stance. Report section 2 (audiences) uses the result, or states that the data cannot answer the question.

A register is a way of writing, not an age. Older people write slang and young people write «увы». The output never
says "zoomers", "pensioners" or an age group as a finding; it says "texts with youth slang", "texts with an older
register". An agent may not predict any person's age, with rules or with a model.

## Inputs (read only these)
- `AGENTS.md` §0, `docs/codebook.md` (stance values), `docs/data_cards/corpus_manifest.md` (slices and their limits)
- `data/processed/corpus_v2.parquet`, `data/processed/corpus_dzen.parquet` (not in git; on this machine)
- `src/analysis/label_sample.py`: import `analysis_slice()`, `CORPUS`, `DZEN` (do not edit the file). The slice is
  5,905 reactions in P3 (YouTube 2,418, Telegram 1,338, VK 1,163, Dzen 986) from 3,180 authors.
- Stance labels: `data/interim/labelling/labels_gemini-3.8-flash.jsonl` (`id`, `stance`, `flags`; D-38). The run ends
  on 2026-10-29; it is complete when it has 1,522 lines. If it is not complete, wait; do not label anything yourself.
  Leave out rows with the flag `off_topic`. The 22 rows of the case thread (column `stratum` in
  `data/interim/labelling/sample.parquet`, D-36) are never mixed into platform figures.

## What is already known (Claude, 2026-10-29, rough regexes on the slice)
- Self-disclosure is rare: about 40 texts of 5,905. Live nearby 13, worked at the plant 6, family worked there 3,
  childhood memories 5, Soviet-time memories 5. Nobody states an age; nobody says «я пенсионер» or «я студент».
- Youth slang (кринж, рофл, чел, лол, ахах, ваще, имхо, база, скуф…) in 58 texts (1.0%); older register (уважаемые,
  господа, увы, с уважением, товарищи, в наше время…) in 76 (1.3%).
- Emoji depend on the platform interface: VK 0.6%, Telegram 8.2%, Dzen 6.9%, YouTube 13.6%. Compare emoji only within a
  platform, never across platforms.
- «зумер», «бумер», «скуф» are mostly said about someone else, as an insult. Count them as "mentions a generation",
  not as a marker of the writer.
Improve these dictionaries; do not assume they are right.

## Method
1. Script `register.py` in this card folder, with `--help`, run from the repo root:
   `.venv/bin/python workflow/stage1/T18_speech_register/register.py`. Fixed seed. Lowercase, `ё` = `е`.
2. Marker families, each a list of regexes in `out/markers.yaml` with 2–3 positive and 2–3 negative test strings per
   regex (invented short strings, not corpus texts):
   - `youth_slang`: words of youth internet slang in the author's own voice;
   - `chat_orthography`: «ахах», «))», «спс», «пж», «кста», whole message lowercase without punctuation (≥ 6 words);
   - `older_register`: formal address and bookish words («уважаемые», «господа», «увы», «с уважением», «благодарю»);
     four or more dots, doubled commas;
   - `generation_mention`: «зумер», «бумер», «скуф», «молодёжь», «старики», «пенсионеры» about others;
   - `self_age`, `self_resident`, `self_worked`, `family_worked`, `childhood_memory`: first-person self-disclosure.
   Run the tests inside the script; exit non-zero if one fails.
3. Hand check of precision. For each family draw 40 random hits (all of them if fewer) into
   `data/interim/register/validation.csv` (`id, family, text, ok, comment`). Read each and set `ok` = 1 if the marker
   is used as the family means it (own voice, not a quote; «увы» counts, «чел» as "person" in slang counts), else 0.
   Precision = mean of `ok`. A family with precision < 0.7 is reported but not used in step 5.
4. Coverage: share of texts and share of authors (an author is covered if any text has the marker), overall and per
   platform. An author can be in several families; say how many are.
5. Crossing with stance, on the labelled sample only (stance from step "Inputs"): for each kept family, the stance
   counts of covered rows against all other labelled rows, per platform and overall. Give a share only where a cell
   has n ≥ 30; else counts only. Add Fisher's exact test (oppose vs not oppose) where both groups have n ≥ 30, and
   say that with many comparisons a single p < 0.05 proves little.
6. Decision rule, fixed before you look at stance: if `youth_slang` + `chat_orthography` together cover < 5% of
   labelled authors, or `older_register` covers < 5%, the age question is `untestable` with this corpus. Then say it in
   one line and stop at coverage and examples. Do not lower the threshold afterwards.
7. Concentration: the largest publication holds 715 of 2,418 YouTube, 365 of 1,338 Telegram and 359 of 1,163 VK
   reactions (`corpus_manifest.md`). Give the coverage per platform with and without its largest publication.

## Output
- `register.py`, `out/markers.yaml` (dictionary and tests)
- `out/coverage.csv`: `family, platform, texts, texts_share, authors, authors_share, precision, kept`
  (`platform` = `all` for totals; `precision` from step 3)
- `out/stance_by_family.csv`: `family, platform, group (covered|other), n, oppose, support, mixed, neutral,
  oppose_share, fisher_p` (shares empty where n < 30)
- `data/interim/register/validation.csv` and any per-row flags: gitignored, never in `out/`
- `HANDOFF.md` per `workflow/templates/HANDOFF.md`, with the verdict on the question in one line:
  `answerable` (with the main numbers and n) or `untestable` (with the coverage that failed the rule), and what the
  data cannot show

## Acceptance criteria
- [ ] A1 every regex has positive and negative tests and the script passes them
- [ ] A2 coverage by texts and by authors, overall and per platform, with and without the largest publication
- [ ] A3 precision from a hand check of 40 hits per family (or all hits); families below 0.7 not used for stance
- [ ] A4 shares only for cells with n ≥ 30; the decision rule of step 6 applied as written
- [ ] A5 no text, quote, name or author hash of a private person in `out/` or `HANDOFF.md` (aggregates only); examples
      in HANDOFF are your paraphrase of at most 10 words
- [ ] A6 no age is assigned to any person; findings speak of registers and self-disclosure, never of age groups
- [ ] A7 `register.py --help` works; a second run gives the same files

## Rules quoted for this card
- R3: never invent numbers or examples. R5: private individuals are not named; texts of private people do not go into
  git (D-24). R8: output exactly this schema; `HANDOFF.md` ≤ 30 lines.
- Write only inside `workflow/stage1/T18_speech_register/` and `data/interim/register/`, and your BOARD row.
