# REVIEW T18 — R1

## Facts and format (Claude; Codex is the worker of this card)
Checked: HANDOFF (26 lines), `out/coverage.csv`, `out/stance_by_family.csv`, `out/markers.yaml`, `register.py --help`.

| Criterion | Pass? | Note |
|-----------|-------|------|
| A1 | yes | 14 regexes with invented positive and negative strings; `--tests-only` exists |
| A2 | yes | texts and authors, overall and per platform, with `:without_largest` rows |
| A3 | yes | 193 hits read; three self-disclosure families below 0.7 are dropped from the stance step |
| A4 | yes | rule of step 6 applied before stance: 16 of 812 labelled authors (1.97%) for youth slang and chat orthography, 32 of 812 (3.94%) for the older register; stance table left empty |
| A5 | yes | no 16-hex author hash, text or name in `out/`; the yaml strings are invented |
| A6 | yes | no age assigned; wording speaks of registers |
| A7 | yes by HANDOFF | two identical runs reported; not re-run by the reviewer |

## Content (Claude)
- The verdict `untestable` answers the user's question honestly: the comments cannot show whether younger or older
  people are more dissatisfied. Absence of markers does not mean that generations agree; HANDOFF says so.
- Useful side result: self-disclosure as a resident is right in only 15 of 29 hits (other districts, other plants).
  Claude's rough count of 13 "live nearby" texts (2026-10-29) overstated it; the report does not use it as a number.
- What replaces it for report section 3: stance by where people talk (`reports/tables/stance_by_segment.csv`) and the
  self-described occupations of the Archi.ru signers (D-42), which include «студент» and «пенсионер».

## Verdict: accept
H9 → `untestable` on the comment corpus; the signer occupations are reported separately.

## Fix list
None.
