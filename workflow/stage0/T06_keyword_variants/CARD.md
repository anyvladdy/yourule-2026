# T06 — Keyword morphology, variants and tested regexes

Reader: worker agent. Human summary of this stage: `workflow/stage0/README.md`.

- **Stage:** 0 · **Worker:** Codex · **Content review:** Claude · **Fallback:** Claude
- **Time box:** 45 min · No web access needed.
- Reassigned from OpenCode/qwen3:8b (D-09): correct Russian inflection and regexes need a script plus judgement.

## Goal
Word forms, spelling variants and a tested regex for every site/actor term, so later queries and filters
neither miss mentions nor match look-alikes (metro station, street, other towns).

## Inputs (read only these)
- `AGENTS.md` §0
- `config/keywords.yaml` — sections `core`, `site_context`, `exclude` (`topic` terms are matched by lemma later; skip them)

## Method
1. Write `make_variants.py` in this card folder. Run it from the repo root with `.venv/bin/python workflow/stage0/T06_keyword_variants/make_variants.py` (same environment as `uv run`).
   Environment is ready: `pymorphy3`, `pymorphy3-dicts-ru`, `pyyaml` (see `pyproject.toml`, `uv.lock`). Install nothing else.
2. Generate singular case forms with pymorphy3. For multi-word terms inflect the head noun and agreeing adjectives;
   keep dependent genitives unchanged ("территория Электрозавода" → "территории Электрозавода", …).
3. Fix pymorphy3 output by hand where it is wrong (proper names, abbreviations like МЭЛЗ). Record each manual fix in `note`.
4. Build one regex per term. Requirements: case-insensitive intent handled explicitly (`[Ээ]`), word boundaries that work
   with Cyrillic (`\b` in Python `re` with Unicode is acceptable; test it), ё/е both accepted where relevant.
5. Tests in the same script: every regex must match all its `case_forms` and `spelling_variants`, and match none of
   its `negative_examples`. Required negatives for Электрозавод terms: "Электрозаводская", "Электрозаводской",
   "Электрозаводск", "электрозаводский". Add obvious negatives for other ambiguous terms (e.g. "Эталон" as a common noun
   is not testable by regex: say so in `note`, the anchor rule in keywords.yaml handles it).
6. The script exits non-zero if any test fails.

## Output
- `make_variants.py`
- `out/variants.yaml`, one entry per input term:
```yaml
- term: "Электрозавод"
  section: core
  case_forms: [...]
  spelling_variants: [...]      # systematic only: ё/е, letter case, hyphenation
  proposed_variants: [...]      # plausible, not confirmed in real texts; checked in the stage-1 pilot
  hashtags: [...]
  regex: "..."
  negative_examples: [...]
  note: ""
```
- `out/test_report.txt`: the script's output (per term: forms matched / negatives rejected; total pass/fail).
- `HANDOFF.md` per `workflow/templates/HANDOFF.md`.

## Acceptance criteria
- [ ] A1 every `core`, `site_context` and `exclude` term appears exactly once
- [ ] A2 singular case forms correct, multi-word terms inflected as phrases; manual fixes noted
- [ ] A3 ё/е variants where relevant (Семёновская / Семеновская)
- [ ] A4 script runs cleanly from the repo root and all regex tests pass; `test_report.txt` matches a fresh run
- [ ] A5 no new search topics invented; unsure variants only in `proposed_variants`
- [ ] A6 `HANDOFF.md` lists any changes you recommend for `config/keywords.yaml` (do not edit it yourself)

## Rules quoted for this card
- Write only inside `workflow/stage0/T06_keyword_variants/` (and your BOARD row).
- Do not edit `config/keywords.yaml`; Claude integrates.
