# T12 — Price benchmarks for the budget lines

Reader: worker agent. Human summary of this stage: `workflow/stage1/README.md`.

- **Stage:** 5 input, run now (Codex review P13) · **Worker:** dsh · **Content review:** Claude · **Fallback:** Claude
- **Time box:** 90 min · **Size cap:** ≤ 50 rows, 1–3 per key
- **No parsing / no scrapers.** Manual browsing and web search only. Do not contact vendors or request quotes.

## Goal
A public, dated price range for every kind of cost in the campaign budget, so each budget line gets a unit cost
with a source. Claude turns the ranges into the budget (`deliverables/budget.csv`); this card does not price lines itself.

## Inputs (read only these)
- `AGENTS.md` §0
- This card. The budget lines are grouped into the keys below; `deliverables/budget.csv` has the full wording if needed.

| Key | What to price (Moscow, 2025–2026) | Budget lines |
|---|---|---|
| K01 | Communications strategy and concept by an agency or consultant: package or day rate | B001, B002 |
| K02 | Explainer diagram or infographic design (1 diagram + adaptations) | B003, B010 |
| K03 | Layout of a leaflet and social-media cards | B004, B012 |
| K04 | Script and storyboard for a short corporate video | B005 |
| K05 | Video shooting day with a small crew (operator, sound, light) | B006 |
| K06 | Editing of a 1–3 min video with subtitles | B007 |
| K07 | Printing of an A5 or A4 leaflet, runs of 1,000–5,000 copies, per copy | B008, B011 |
| K08 | Leaflet distribution to mailboxes in Moscow, per 1,000 | B009 |
| K09 | Paid distribution in VK Ads, Telegram Ads, Yandex Direct: CPM or CPC, Moscow targeting | B013–B016 |
| K10 | Media and social-media monitoring subscription (e.g. Медиалогия, Brand Analytics, Крибрум, IQBuzz), per month | B017–B021 |
| K11 | Lawyer review of public texts: hourly or package rate | B024, B029, B030 |
| K12 | Heritage expert review of a text (architectural historian, expert in historical and cultural expertise) | B025 |
| K13 | Media training for company speakers, per session | B026 |
| K14 | Ad labelling (ОРД operator fees) and any mandatory payment on internet advertising in 2026 | B031–B034 |
| K15 | Venue hire for a public meeting of 100–200 people with sound, per event | B022, B023 |
| K16 | Professional moderator for a public meeting, per event | B027, B028 |
| K17 | Monthly salary in Moscow: PR campaign lead; PR/media editor; analyst or community manager | B035–B049 |
| K18 | Pay rule for work on non-working public holidays (law) | B050, B051 |
| K19 | Employer insurance contribution rates in 2026 (law) | B052, B054, B056, B058, B060 |
| K20 | VAT rate in 2026 (law) | B053, B055, B057, B059, B061 |

## Output
`out/prices.csv` with exactly these columns:
`key, what_priced, unit, price_low_rub, price_high_rub, vat, region, source_url, source_type, source_date, accessed, label, note`
- `vat`: `incl` | `excl` | `none` | `unknown`
- `source_type`: `price_list` | `rate_card` | `procurement` | `salary_stats` | `law` | `article`
- `source_date`: when the price was published or valid (YYYY-MM or YYYY-MM-DD); `unknown` if not shown
- `label`: `fact` for a price or rate as published; `proxy` for a near substitute (other city, other year, similar service)
- K18–K20: put the rate or rule in `what_priced` and `note`, leave the price columns empty.
- `HANDOFF.md` per `workflow/templates/HANDOFF.md`.

## Acceptance criteria
- [ ] A1 every key K01–K20 has at least one row, or one row with `note = not_found` and the queries tried
- [ ] A2 every URL opened in this session; no invented prices, names or rates
- [ ] A3 each price states its unit and whether VAT is included; ranges come from published numbers, not guesses
- [ ] A4 prices older than 2025 or from outside Moscow are labelled `proxy` with the reason in `note`
- [ ] A5 public procurement records (zakupki.gov.ru) are welcome for K01, K05–K08, K13, K15, K16; give the contract
      or tender number in `note`
- [ ] A6 HANDOFF names the five keys with the weakest evidence

## Rules quoted for this card
- R3: never invent sources or numbers; `not_found` is a valid result.
- R5: public content only; no personal data of private people (salary surveys are aggregates; do not copy CVs).
- Write only inside `workflow/stage1/T12_price_benchmarks/` and your BOARD row.
