"""Public attention by week (Yandex Wordstat) against the event timeline: spikes and their triggers.

Run from the repository root with .venv/bin/python. Reads the three Wordstat exports made by the user on 2026-10-28
(Tasks_for_humans_exported/wordstat_dynamic*.xlsx: «Электрозавод», «Электрозавод снос», «Электрозавод Эталон»;
Moscow and Moscow region, all devices, weeks from 2024-09-30) and docs/project_facts/timeline.csv.
Writes reports/tables/attention_weekly.csv and reports/tables/attention_spikes.csv; aggregates only.

Baseline: median weekly count from 2024-09-30 to 2025-01-31, before the fire. A spike is a week at least twice the
baseline of «Электрозавод». Events within the spike week or the 6 days before it are listed next to it; timing
alone does not show that an event caused the spike. Google Trends exports are not used: region Russia only,
from 2026-07-31, and 75 of 90 days are zero.
"""
import argparse
import glob
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EXPORTS = ROOT / 'Tasks_for_humans_exported'
TIMELINE = ROOT / 'docs/project_facts/timeline.csv'
OUT = ROOT / 'reports/tables'
MAIN = 'Электрозавод'


def load_wordstat():
    series = {}
    for path in sorted(glob.glob(str(EXPORTS / 'wordstat_dynamic*.xlsx'))):
        sheet = pd.read_excel(path, header=None)
        query = re.search(r'«(.+?)»', str(sheet.iloc[0, 3])).group(1)
        weeks = sheet.iloc[1:, :2].copy()
        weeks.columns = ['week', 'n']
        # Wordstat stamps each week with its Sunday 23:59; the week starts on the Monday after that stamp's date.
        weeks['week'] = pd.to_datetime(weeks.week).dt.normalize() + pd.Timedelta(days=1)
        series[query] = weeks.set_index('week').n.astype(int)
    return pd.DataFrame(series).sort_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--factor', type=float, default=2.0, help='spike = week ≥ factor × baseline (default 2)')
    args = parser.parse_args()
    weekly = load_wordstat()
    baseline = weekly.loc['2024-09-30':'2025-01-31'].median()
    weekly[f'{MAIN} × baseline'] = (weekly[MAIN] / baseline[MAIN]).round(2)
    events = pd.read_csv(TIMELINE)
    events = events[events.date.str.len() == 10].assign(day=lambda e: pd.to_datetime(e.date))

    spikes = []
    for week, row in weekly[weekly[MAIN] >= args.factor * baseline[MAIN]].iterrows():
        near = events[(events.day >= week - pd.Timedelta(days=6)) & (events.day <= week + pd.Timedelta(days=6))]
        spikes.append({'week': week.date(), **{q: row[q] for q in baseline.index}, 'times_baseline': row[f'{MAIN} × baseline'],
                       'events_in_or_before_week': ' | '.join(f'{d.date()} {t[:90]}' for d, t in zip(near.day, near.event))})
    spikes = pd.DataFrame(spikes)
    OUT.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(OUT / 'attention_weekly.csv', index_label='week')
    spikes.to_csv(OUT / 'attention_spikes.csv', index=False)
    print('baseline (median per week, 2024-09-30 – 2025-01-31):', baseline.to_dict())
    print(spikes.drop(columns='events_in_or_before_week').to_string(index=False))
    for period, (start, end) in {'after the fire': ('2025-02-03', '2025-04-27'), 'quiet': ('2025-05-01', '2026-06-07'),
                                 'conflict': ('2026-06-08', '2026-09-28')}.items():
        part = weekly.loc[start:end]
        print(f'{period:15s} {start} – {end}: weeks {len(part)}, total {part[MAIN].sum():,}, '
              f'«снос» {part["Электрозавод снос"].sum():,}, «Эталон» {part["Электрозавод Эталон"].sum():,}')
    print('written: reports/tables/attention_weekly.csv, reports/tables/attention_spikes.csv')


if __name__ == '__main__':
    main()
