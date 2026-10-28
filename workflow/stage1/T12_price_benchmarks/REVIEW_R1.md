# REVIEW R1 — T12 price benchmarks

Reviewer: Claude (facts and content; Codex busy with T11, D-11 practice). Date: 2026-10-28.

## Facts and format
- `out/prices.csv`: 30 rows, 13 columns as in the card, keys K01–K20 all present. Units and `vat` filled in every row.
- Checked against the source, opened 2026-10-28 (5 rows, all numbers that will reach the report as rates or anchors):
  - K20: VAT 22% from 01.01.2026, Federal Law of 28.11.2025 № 425-ФЗ (nalog.gov.ru): confirmed.
  - K19: 30% within the base, 15.1% above; the page also gives the 2026 base, 2,979,000 RUB per person: confirmed.
    The page is marked as archived; the rates match the row.
  - K01: AKAR study, average communications strategy 1.88 million RUB in 2025: confirmed.
  - K15: Академия Кантаты, hall 9, 200 people: the page says 7,500–8,500 RUB per hour, minimum 5 hours
    (another line on the page says 3). The row gives 7,500–7,500. Correction C1 below.
- `tools/fetch_one_page.py` reads one page per run, no crawling. A small deviation from "no parsing"; declared in HANDOFF; accepted.

## Content
Useful and enough to price every budget line with a stated source. Weak points, handled in the budget, not by a new round:
- K01 is an agency average for a full package. Our strategy line covers consultants who also work on payroll lines, so
  the budget uses a reduced share of it, labelled `inference`.
- K17 salaries are medians of vacancy offers. A campaign lead for a public conflict is above the median; the budget uses
  the upper part of the range, labelled `inference`.
- K10 has only IQBuzz entry tier; a monitoring service of the needed depth costs more. Budget labels its figure `proxy`.
- VAT is `unknown` for most commercial prices; the budget treats them as excluding VAT and adds 22% once (conservative).

## Verdict: accept (D-13)
Corrections applied by Claude in the integrated budget, worker output unchanged:
- C1 K15: price range 7,500–8,500 RUB per hour, minimum 5 hours (3 hours also mentioned on the page).
