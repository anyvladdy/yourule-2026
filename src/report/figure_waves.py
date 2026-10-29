"""Figure 1 of the report: weekly Yandex searches for «Электрозавод» and weekly signatures under the Archi.ru letter,
June – October 2026, with the events that preceded each wave.

Run from the repository root after attention_timeline.py and petition_signers.py:
.venv/bin/python src/report/figure_waves.py  →  reports/figures/fig1_waves.png (aggregates only).
Two panels instead of one chart with two y-axes: the measures have different scales. One hue for both series,
text in ink colours, events as thin grey lines with short labels.
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / 'reports/tables'
SERIES, INK, INK_2, GRID, SURFACE = '#2a78d6', '#0b0b0b', '#52514e', '#e4e3df', '#ffffff'
START, END = pd.Timestamp('2026-06-01'), pd.Timestamp('2026-11-01')
EVENTS = [('2026-06-15', 'текст «Архи.ру» о сносе'), ('2026-06-24', 'ответ компании и открытое письмо'),
          ('2026-07-08', 'кассационный суд'), ('2026-09-07', 'фото сноса в соцсетях')]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', default=str(ROOT / 'reports/figures/fig1_waves.png'), help='output PNG path')
    args = parser.parse_args()
    weekly = pd.read_csv(TABLES / 'attention_weekly.csv', parse_dates=['week']).set_index('week')
    search = weekly.loc[START:END, 'Электрозавод']
    daily = pd.read_csv(TABLES / 'petition_daily.csv', parse_dates=['day']).set_index('day').signatures
    # weeks from Monday, as in Wordstat
    signatures = daily.groupby(daily.index - pd.to_timedelta(daily.index.day_of_week, unit='D')).sum().loc[START:END]

    plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 10, 'axes.edgecolor': GRID,
                         'axes.labelcolor': INK_2, 'xtick.color': INK_2, 'ytick.color': INK_2})
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(6.3, 4.4), sharex=True, dpi=220,
                                      gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.35})
    fig.patch.set_facecolor(SURFACE)
    top.plot(search.index, search.values, color=SERIES, linewidth=2, solid_capstyle='round')
    top.scatter(search.index, search.values, color=SERIES, s=10, zorder=3, edgecolors=SURFACE, linewidths=1)
    bottom.bar(signatures.index, signatures.values, width=5, color=SERIES, edgecolor=SURFACE, linewidth=1, align='edge',
               zorder=2)

    top.set_title('Поиск «Электрозавод» в Яндексе, запросов в неделю (Москва и область)', loc='left', color=INK, fontsize=10)
    bottom.set_title('Подписи под письмом «Архи.ру», в неделю', loc='left', color=INK, fontsize=10)
    for axis in (top, bottom):
        axis.set_facecolor(SURFACE)
        axis.grid(axis='y', color=GRID, linewidth=0.6)
        axis.set_axisbelow(True)
        for side in ('top', 'right', 'left'):
            axis.spines[side].set_visible(False)
        axis.tick_params(length=0)
        axis.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:,.0f}'.replace(',', ' ')))
        for day, _ in EVENTS:
            axis.axvline(pd.Timestamp(day), color=INK_2, linewidth=0.6, linestyle=(0, (2, 2)), zorder=1)
    for number, (day, _) in enumerate(EVENTS, 1):
        top.text(pd.Timestamp(day), search.max() * 1.36, str(number), color=INK, fontsize=8, ha='center', va='center',
                 bbox={'boxstyle': 'circle,pad=0.25', 'facecolor': SURFACE, 'edgecolor': INK_2, 'linewidth': 0.6})
    top.set_ylim(0, search.max() * 1.46)
    # selective direct labels: the peak of each panel and the September search wave
    for week in (search.idxmax(), pd.Timestamp('2026-09-07')):
        top.annotate(f'{search[week]:,}'.replace(',', ' '), (week, search[week]), textcoords='offset points',
                     xytext=(0, 5), color=INK, fontsize=8, ha='center', va='bottom', zorder=4,
                     bbox={'boxstyle': 'square,pad=0.15', 'facecolor': SURFACE, 'edgecolor': 'none'})
    for week in signatures.nlargest(2).index:
        bottom.annotate(f'{signatures[week]:,}'.replace(',', ' '), (week + pd.Timedelta(days=2.5), signatures[week]),
                        textcoords='offset points', xytext=(0, 3), ha='center', color=INK, fontsize=8, zorder=4,
                        bbox={'boxstyle': 'square,pad=0.15', 'facecolor': SURFACE, 'edgecolor': 'none'})
    bottom.set_ylim(0, signatures.max() * 1.2)
    bottom.xaxis.set_major_locator(mdates.MonthLocator())
    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    bottom.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: months[mdates.num2date(v).month - 1]))
    bottom.set_xlim(START, END)
    legend = '; '.join(f'{n} — {label} ({pd.Timestamp(day):%d.%m})' for n, (day, label) in enumerate(EVENTS, 1))
    fig.text(0.01, 0.035, 'События: ' + legend + '.', fontsize=7, color=INK_2)
    fig.text(0.01, 0.005, 'Источники: Яндекс Wordstat (по неделям, данные до 04.10.2026); список подписей «Архи.ру» '
             '(19 752 подписи, 25.06–28.10.2026).', fontsize=7, color=INK_2)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, bbox_inches='tight', facecolor=SURFACE)
    print('written', args.out)


if __name__ == '__main__':
    main()
