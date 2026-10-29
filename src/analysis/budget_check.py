"""Compute the campaign budget from deliverables/budget.csv and check the 10,000,000 RUB limit.

Run from the repository root. Lines are priced as unit_cost_rub × qty, except:
  Страховые взносы  = --insurance-rate × payroll (Оплата труда) of the same month
  НДС               = --vat-rate × purchases of the same month (all lines except payroll, contributions, VAT, reserve)
  Резерв            = --reserve-share × everything else, unless the line has its own price
Each line is rounded to whole roubles before summing, so the CSV lines add up to the printed total.
Prints totals by category and by month and lists lines that still miss a price or a quantity.
Exit code 1 if the total is over the limit or a rate is missing; --write fills total_rub in the CSV.
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUDGET = ROOT / 'deliverables/budget.csv'
LIMIT = 10_000_000
PAYROLL, INSURANCE, VAT, RESERVE = 'Оплата труда', 'Страховые взносы', 'НДС', 'Резерв'


def number(value):
    return float(value.replace(' ', '').replace(',', '.')) if value and value.strip() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--vat-rate', type=float, help='e.g. 0.22; source must be in T12 (K20)')
    parser.add_argument('--insurance-rate', type=float, help='effective employer rate, e.g. 0.30; source in T12 (K19)')
    parser.add_argument('--reserve-share', type=float, default=0.0, help='reserve as a share of all other costs')
    parser.add_argument('--write', action='store_true', help='write computed total_rub back to the CSV')
    args = parser.parse_args()

    with BUDGET.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)

    missing, totals = [], {}
    payroll, purchases = defaultdict(float), defaultdict(float)
    for row in rows:
        if row['category'] in (INSURANCE, VAT, RESERVE):
            continue
        cost, qty = number(row['unit_cost_rub']), number(row['qty'])
        if cost is None or qty is None:
            missing.append(row['line_id'])
            continue
        totals[row['line_id']] = round(cost * qty)
        (payroll if row['category'] == PAYROLL else purchases)[row['phase']] += cost * qty

    problems = set()
    for row in rows:
        rate = {INSURANCE: args.insurance_rate, VAT: args.vat_rate}.get(row['category'])
        if row['category'] in (INSURANCE, VAT):
            if rate is None:
                problems.add(f'{row["category"]}: rate not set')
                continue
            base = payroll if row['category'] == INSURANCE else purchases
            totals[row['line_id']] = round(rate * base[row['phase']])
    for category, base in ((INSURANCE, payroll), (VAT, purchases)):
        lines = {row['phase'] for row in rows if row['category'] == category}
        problems |= {f'{category}: no line for {phase}, its base is not taxed' for phase in base if phase not in lines}
    subtotal = sum(totals.values())
    for row in rows:
        if row['category'] == RESERVE:
            own = number(row['unit_cost_rub'])
            totals[row['line_id']] = round(own * (number(row['qty']) or 1) if own is not None
                                           else args.reserve_share * subtotal)

    by_category, by_month = defaultdict(float), defaultdict(float)
    for row in rows:
        if row['line_id'] in totals:
            by_category[row['category']] += totals[row['line_id']]
            by_month[row['phase']] += totals[row['line_id']]
    total = sum(totals.values())

    print('By category:')
    for name, value in sorted(by_category.items(), key=lambda item: -item[1]):
        print(f'  {name:<40} {value:>14,.0f}')
    print('By month:')
    for name, value in by_month.items():
        print(f'  {name:<40} {value:>14,.0f}')
    print(f'Total {total:,.0f} RUB of {LIMIT:,} ({total / LIMIT:.1%}); headroom {LIMIT - total:,.0f}')
    if missing:
        print(f'Not priced yet ({len(missing)}): {", ".join(missing)}')
    for problem in problems:
        print(problem)

    if args.write:
        for row in rows:
            if row['line_id'] in totals:
                row['total_rub'] = f'{totals[row["line_id"]]:.0f}'
        with BUDGET.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    return 1 if total > LIMIT or problems else 0


if __name__ == '__main__':
    sys.exit(main())
