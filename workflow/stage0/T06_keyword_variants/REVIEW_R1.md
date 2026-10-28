# REVIEW T06 — R1

Codex was the worker on this card, so Claude did both parts of the review.

## Facts and format (Claude, standing in for Codex)
Checks: fresh run of `make_variants.py` from the repo root (exit 0, report identical to the saved one);
term coverage against `config/keywords.yaml` (22/22, none missing); 13 new test strings not in the script.

| Criterion | Pass? | Note |
|-----------|-------|------|
| A1 | yes | 22 of 22 terms, each once |
| A2 | yes | spot-checked Электрозавод, Московский электрозавод, территория Электрозавода, Соколиная Гора, МЭЛЗ; manual fixes noted (МЭЛЗ was parsed as a female name by pymorphy3) |
| A3 | yes | Семёновская / Семеновская both covered |
| A4 | yes | reproducible; new strings behaved as expected: "На Электрозаводе", "ЭЛЕКТРОЗАВОДА", "на Соколиной горе" match; "Электрозаводской улицы", "Электрозаводский мост", "Электрозаводск", "Соколиногорский" do not |
| A5 | yes | unconfirmed hyphenated spellings kept in `proposed_variants` only |
| A6 | yes | recommendations listed in HANDOFF |

## Content (Claude)
- Fit for stage 1. The two deviations are reasonable: "Эталон Электрозавод" is better as a co-mention of two words
  than as a phrase, and the "Электрозаводская" negatives only apply to the Электрозавод noun terms.
- Plural forms ("электрозаводы") are not matched. Acceptable: the card asked for singular, and the site is singular.
- The regexes spell out each letter as a character class (`[Ээ][Лл]…`), which works but is hard to read.
  Stage 1 collectors should build patterns from `case_forms` with `re.IGNORECASE` instead of copying these strings.
  Not a fix item; noted for the stage-1 cards.
- Usage in real texts is untested (no web, by design). The stage-1 pilot checks it.

## Verdict: accept

## Fix list
none

## Integration
- `out/variants.yaml` becomes the reference word-form list; `config/keywords.yaml` points to it.
- Applied HANDOFF recommendation: "Эталон Электрозавод" moved from a literal phrase to a co-mention rule.
