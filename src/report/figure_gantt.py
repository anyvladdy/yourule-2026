"""Campaign calendar as a week-by-week chart (appendix Г and the separate timeline file).

Reads deliverables/roadmap.csv. Each step is one bar from its week_start to the end of that week; rows are grouped by
work stream, the stream sets the bar colour and is named in the legend and on the left. Vertical lines mark the
public milestones, the grey band the New Year holidays. Every row carries its text label, and the table in
appendix Г repeats the data, so colour never carries meaning alone.

Run from the repository root:
.venv/bin/python src/report/figure_gantt.py
  → reports/figures/fig_gantt.png (for the Word file) and deliverables/appendix_timeline.pdf (separate file).
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[2]
INK, INK_2, GRID, SURFACE, BAND = '#0b0b0b', '#52514e', '#e4e3df', '#ffffff', '#f1f0ec'

# fixed categorical order (validated with the dataviz validator, light mode)
STREAMS = [
    ('Раскрытие и материалы', '#2a78d6', ['R00', 'R01', 'R35', 'R04', 'R06', 'R07', 'R32', 'R34', 'R08', 'R09',
                                          'R11', 'R14', 'R19', 'R22']),
    ('Встречи с жителями', '#eb6834', ['R10', 'R12', 'R13', 'R15', 'R16', 'R43', 'R44', 'R21', 'R45', 'R23',
                                       'R24']),
    ('Экспертный совет', '#1baf7a', ['R36', 'R37', 'R38', 'R39']),
    ('Замеры и обращения', '#eda100', ['R02', 'R31', 'R17', 'R18', 'R20', 'R33', 'R26']),
    ('Животные на площадке', '#e87ba4', ['R40', 'R41', 'R42']),
    ('Бывшие арендаторы', '#008300', ['R46', 'R47']),
    ('Управление и закрытие', '#6250d6', ['R03', 'R05', 'R25', 'R27', 'R28', 'R29', 'R30']),
]
MILESTONES = [('2026-11-01', 'старт'), ('2026-11-23', 'схема'), ('2026-12-17', 'встреча'),
              ('2027-01-28', 'жители'), ('2027-02-11', 'жители'), ('2027-02-18', 'встреча'),
              ('2027-02-26', 'конец этапа')]
HOLIDAYS = ('2026-12-31', '2027-01-12')
# steps that run longer than their first week: until this date
SPANS = {'R34': '2027-02-26', 'R40': '2027-01-15'}


def short(text, limit=78):
    text = text.split(':', 1)[1].strip() if ':' in text[:5] else text
    return text if len(text) <= limit else text[:limit - 1].rstrip(' ;,') + '…'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--png', default=str(ROOT / 'reports/figures/fig_gantt.png'))
    parser.add_argument('--pdf', default=str(ROOT / 'deliverables/appendix_timeline.pdf'))
    args = parser.parse_args()

    road = pd.read_csv(ROOT / 'deliverables/roadmap.csv')
    road['code'] = road['activity'].str.extract(r'^(R\d+)')
    road = road.set_index('code')
    listed = [c for _, _, codes in STREAMS for c in codes]
    missing = sorted(set(road.index) - set(listed))
    if missing:
        raise SystemExit(f'steps without a stream: {missing}')

    rows = []
    for name, colour, codes in STREAMS:
        for c in sorted(codes, key=lambda c: (road.loc[c, 'week_start'], int(c[1:]))):
            rows.append((c, name, colour, pd.Timestamp(road.loc[c, 'week_start']), short(road.loc[c, 'activity'])))

    plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 7})
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(SURFACE)
    n = len(rows)
    ax.axvspan(pd.Timestamp(HOLIDAYS[0]), pd.Timestamp(HOLIDAYS[1]), color=BAND, zorder=0)
    ax.text(pd.Timestamp('2027-01-05'), -0.9, 'праздники', ha='center', va='center', color=INK_2, fontsize=6.5)
    for d, label in MILESTONES:
        x = pd.Timestamp(d)
        ax.axvline(x, color=INK_2, lw=0.6, ls=(0, (2, 2)), zorder=1)
        ax.text(x, n - 0.1, f'{x:%d.%m} {label}', rotation=90, ha='right', va='top', fontsize=6, color=INK_2)
    prev = None
    for i, (code, stream, colour, start, label) in enumerate(rows):
        if prev is not None and stream != prev:
            ax.axhline(i - 0.5, color=GRID, lw=0.8, zorder=1)
        prev = stream
        end = pd.Timestamp(SPANS[code]) if code in SPANS else start + pd.Timedelta(days=6)
        ax.barh(i, end - start, left=start + pd.Timedelta(hours=12), height=0.62, color=colour,
                edgecolor=SURFACE, linewidth=1, zorder=2)
        ax.text(pd.Timestamp('2026-10-24'), i, f'{code}  {label}', ha='right', va='center', color=INK, fontsize=6.6)
    ax.set_ylim(n + 4.2, -1.4)
    ax.set_xlim(pd.Timestamp('2026-10-26'), pd.Timestamp('2027-04-05'))
    ax.set_yticks([])
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.xaxis.tick_top()
    ax.tick_params(axis='x', labelsize=6.3, colors=INK_2, length=2, rotation=90)
    ax.grid(axis='x', color=GRID, lw=0.4, zorder=0)
    for side in ('left', 'right', 'bottom'):
        ax.spines[side].set_visible(False)
    ax.spines['top'].set_color(GRID)
    handles = [Patch(facecolor=c, label=s) for s, c, _ in STREAMS]
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.005), ncol=4, frameon=False,
              fontsize=7, handlelength=1.2, columnspacing=1.2)
    fig.suptitle('Календарь кампании по неделям, 26.10.2026 – 31.03.2027 (шаги R00–R47)',
                 x=0.5, y=0.985, fontsize=9, color=INK)
    fig.subplots_adjust(left=0.43, right=0.985, top=0.9, bottom=0.07)
    for out in (args.png, args.pdf):
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=220, facecolor=SURFACE)
    print(f'{n} steps → {args.png}, {args.pdf}')


if __name__ == '__main__':
    main()
