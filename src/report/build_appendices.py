"""Build the table appendices of the report as drafts in deliverables/drafts/ (same format as the other drafts).

Run from the repository root after budget_check.py --write and figure_gantt.py:
.venv/bin/python src/report/build_appendices.py
  → appendix_c_budget.md    (Приложение В: бюджет по статьям, месяцам и строкам, допущения)
    appendix_d_calendar.md  (Приложение Г: календарь, рисунок и таблица шагов)
    appendix_f_sources.md   (Приложение Е: источники фактов основного текста и цен бюджета)
Text between <!-- text --> marks goes into the Word file; the notes below it do not.
"""
import argparse
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DRAFTS = ROOT / 'deliverables/drafts'
MONTHS = {'Oct 2026': 'октябрь 2026', 'Nov 2026': 'ноябрь 2026', 'Dec 2026': 'декабрь 2026',
          'Jan 2027': 'январь 2027', 'Feb 2027': 'февраль 2027', 'Mar 2027': 'март 2027'}
SECTIONS = {'s1': '1', 's2': '2', 's3': '3', 's4': '4', 's5': '5', 'appendix_b': 'Прил. Б'}
TAXES = ('НДС', 'Страховые взносы', 'Резерв')


def rub(x):
    return f'{x:,.0f}'.replace(',', ' ')


def cell(text):
    # the CSV files use '; ' where a comma would break an unquoted field
    return str(text).replace('|', '/').replace('\n', ' ').replace('; ', ', ').strip()


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(cell(v) for v in r) + ' |' for r in rows]
    return '\n'.join(out)


def basis(source, category):
    source = str(source)
    if category in TAXES:
        return 'расчёт'
    if source.startswith('как '):
        return source
    if 'fact' in source and 'inference' in source:
        return 'открытая цена с поправкой'
    if 'fact' in source:
        return 'открытая цена'
    if 'proxy' in source:
        return 'близкая открытая цена'
    return 'допущение'


def write(name, title, text, notes):
    body = f'# {title} (собрано скриптом `src/report/build_appendices.py`)\n\nПриложение вне лимита. Текст — между метками.\n\n' \
           f'<!-- text -->\n{text.strip()}\n<!-- /text -->\n\n## Основания (в отчёт не входит)\n{notes.strip()}\n'
    (DRAFTS / name).write_text(body, encoding='utf-8')
    print(f'{name}: {len(text):,} characters')


def budget():
    b = pd.read_csv(ROOT / 'deliverables/budget.csv')
    total = int(b.total_rub.sum())
    by_cat = b.groupby('category', sort=False).total_rub.sum().sort_values(ascending=False)
    by_month = b.groupby('phase', sort=False).total_rub.sum()
    lines = b.copy()
    lines['month'] = lines.phase.map(MONTHS)
    lines = lines.sort_values(['phase'], key=lambda s: s.map(list(MONTHS).index), kind='stable')
    rows = []
    for r in lines.itertuples():
        price = '' if pd.isna(r.unit_cost_rub) else rub(r.unit_cost_rub) if float(r.unit_cost_rub).is_integer() \
            else f'{r.unit_cost_rub:.2f}'.replace('.', ',')
        qty = '' if r.category in TAXES else f'{r.qty:g}'.replace('.', ',')
        rows.append([r.line_id, r.month, r.item, r.unit if r.category not in TAXES else '', price, qty,
                     rub(r.total_rub), basis(r.cost_source, r.category)])
    text = f"""## Приложение В. Бюджет

Итог кампании {rub(total)} ₽ из 10 000 000 ₽ с налогом на добавленную стоимость (НДС), страховыми взносами и резервом; \
свободно {rub(10_000_000 - total)} ₽. Цены услуг указаны без НДС. НДС 22% начисляется раз в месяц на закупки месяца, \
страховые взносы 30% — на оплату труда месяца, резерв — 10% от всех остальных расходов. Каждая строка округлена до \
рубля, сумма строк равна итогу. Цены взяты из открытых прайсов, закупок и зарплатной статистики Москвы за октябрь \
2026 года (приложение Е); где открытой цены нет, стоит допущение.

По статьям:

{table(['Статья', 'Сумма, ₽', 'Доля'], [[c, rub(v), f'{v / total:.1%}'.replace('.', ',')] for c, v in by_cat.items()])}

По месяцам:

{table(['Месяц', 'Сумма, ₽'], [[MONTHS[m], rub(v)] for m, v in by_month.items()])}

Главные допущения:
1. Команда кампании из трёх человек работает с ноября по март, в марте с неполной загрузкой; ставки — по медианам \
зарплатных предложений в Москве.
2. Дежурство в новогодние праздники оплачивается не менее чем в двойном размере, как требует Трудовой кодекс.
3. Цена схемы по корпусам, страницы проекта и стратегии — допущения: публичных цен для таких работ нет.
4. Лечение и передержку животных с площадки оплачивает компания из расходов на площадку, в бюджет кампании они не \
входят. Только стерилизация около 50 кошек стоит 100–400 тыс. ₽.
5. Право первой заявки на студии для бывших арендаторов — решение заказчика, а не расход кампании.
6. Резерв {rub(b.loc[b.category == 'Резерв', 'total_rub'].sum())} ₽ покрывает непредвиденные расходы: \
идёт суд, снос виден на фото, цены подрядчиков уточняются сметами в ноябре.

Все строки:

{table(['№', 'Месяц', 'Статья расходов', 'Единица', 'Цена, ₽', 'Кол-во', 'Сумма, ₽', 'Основание цены'], rows)}
"""
    notes = f"""- Данные: `deliverables/budget.csv`, пересчёт `src/analysis/budget_check.py --vat-rate 0.22 --insurance-rate \
0.30 --reserve-share 0.10 --write`. Строк {len(b)}, итог {rub(total)} ₽.
- Цены и источники строк: колонка `cost_source`, T12 (`workflow/stage1/T12_price_benchmarks/out/prices.csv`), D-40.
- Ставки: НДС K20, взносы K19, праздничная оплата K18 (T12). Стерилизация: zoon.ru, 2026-10-29 (D-51).
"""
    write('appendix_c_budget.md', 'Приложение В — бюджет', text, notes)


def calendar():
    r = pd.read_csv(ROOT / 'deliverables/roadmap.csv')
    rows = []
    for x in r.itertuples():
        code, what = x.activity.split(':', 1)
        rows.append([code, pd.Timestamp(x.week_start).strftime('%d.%m.%y'), what.strip(), x.owner_role,
                     x.deliverable, x.kpi])
    text = f"""## Приложение Г. Календарь кампании

{len(r)} шагов с 26.10.2026 по 31.03.2027. На каждое согласование у заказчика заложено пять рабочих дней, с 31.12 по \
11.01 работает только дежурство. Диаграмма по неделям — рис. Г1, она же отдельным файлом appendix_timeline.pdf.

[[pagebreak]]
[[figure:reports/figures/fig_gantt.png|Рис. Г1. Календарь кампании по неделям. Цвет — направление работы, пунктир — \
публичные даты, серая полоса — новогодние праздники|15.8]]

{table(['№', 'Неделя', 'Что делаем', 'Кто отвечает', 'Результат', 'Показатель'], rows)}
"""
    notes = """- Данные: `deliverables/roadmap.csv` (R00–R47). Рисунок: `src/report/figure_gantt.py`.
- Пять рабочих дней на согласование и праздничное дежурство: SKELETON_NOTES. Новые шаги: D-48 (совет), D-50 (схема),
  D-51 (животные, встречи с жителями, бывшие арендаторы).
"""
    write('appendix_d_calendar.md', 'Приложение Г — календарь', text, notes)


def sources():
    f = pd.read_csv(ROOT / 'docs/report_fact_check.csv', dtype=str).fillna('')
    rows = [[SECTIONS.get(x.section, x.section), x.claim, x.source_url, x.source_date or '—', x.accessed]
            for x in f.itertuples() if x.section in SECTIONS]
    p = pd.read_csv(ROOT / 'workflow/stage1/T12_price_benchmarks/out/prices.csv', dtype=str).fillna('')
    used = sorted(set(re.findall(r'K\d+', ' '.join(pd.read_csv(ROOT / 'deliverables/budget.csv').cost_source.fillna('')))))
    prices = []
    for key in used:
        first = p[p.key == key].iloc[0]
        rng = first.price_low_rub if first.price_low_rub == first.price_high_rub else \
            f'{first.price_low_rub}–{first.price_high_rub}'
        prices.append([first.what_priced, f'{rng} ₽' if rng else 'ставка', first.source_url, first.accessed])
    text = f"""## Приложение Е. Источники

Факты основного текста. «Открыто» — дата, когда источник открыли последний раз. Всего исследование опирается на \
{count_sources()} ссылки, полный список хранится в рабочих материалах.

{table(['Раздел', 'Факт', 'Источник', 'Опубликовано', 'Открыто'], rows)}

Цены бюджета (приложение В):

{table(['Что оценено', 'Цена', 'Источник', 'Открыто'], prices)}
"""
    notes = """- Факты: `docs/report_fact_check.csv` (D-45). Цены: T12 `prices.csv`, первая строка каждого ключа.
- Полный список: `docs/sources.md` (`src/report/sources.py`).
"""
    write('appendix_f_sources.md', 'Приложение Е — источники', text, notes)


def count_sources():
    text = (ROOT / 'docs/sources.md').read_text(encoding='utf-8')
    m = re.search(r'(\d[\d\s]*) (?:URL|ссыл)', text)
    return m.group(1).strip() if m else len(set(re.findall(r'https?://\S+', text)))


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    budget()
    calendar()
    sources()


if __name__ == '__main__':
    main()
