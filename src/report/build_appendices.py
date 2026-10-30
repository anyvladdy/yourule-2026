"""Build the table appendices of the report as drafts in deliverables/drafts/ (same format as the other drafts).

Run from the repository root after budget_check.py --write (both budget tables) and figure_gantt.py:
.venv/bin/python src/report/build_appendices.py
  → appendix_c_budget.md    (Приложение В1: бюджет, вариант А — с работой консультантов)
    appendix_c2_budget_b.md (Приложение В2: бюджет, вариант Б — без работы консультантов)
    appendix_d_calendar.md  (Приложение Г: календарь, рисунок и таблица шагов)
    appendix_f_sources.md   (Приложение Е: источники фактов, данные исследования, цены бюджета)
Text between <!-- text --> marks goes into the Word file; the notes below it do not.
"""
import argparse
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DRAFTS = ROOT / 'deliverables/drafts'
BUDGET_A = ROOT / 'deliverables/budget.csv'
BUDGET_B = ROOT / 'deliverables/budget_variant_b.csv'
MONTHS = {'Oct 2026': 'октябрь 2026', 'Nov 2026': 'ноябрь 2026', 'Dec 2026': 'декабрь 2026',
          'Jan 2027': 'январь 2027', 'Feb 2027': 'февраль 2027', 'Mar 2027': 'март 2027'}
# section labels in docs/report_fact_check.csv → label in the appendix
SECTIONS = {'s1': '1', 's2': '2', 's3': '3', 's4': '4', 's5': '5', 'прил. а': 'Прил. А', 'appendix_b': 'Прил. Б',
            'прил. г': 'Прил. Г'}
TAXES = ('НДС', 'Страховые взносы', 'Резерв')
STRATEGY = 'Разработка стратегии и концепции'
# what variant B buys with the consultants' money, and why (keyed by line id)
WHY_B = {
    'B080': 'главное обвинение — утрата наследия; доказательство, которое не зависит от пресс-службы',
    'B081': 'волны внимания приходят после фото сноса; объяснение стоит там, где снимают',
    'B078': 'позиции аудиторий известны только по соцсетям; проверить сообщения и схему на жителях',
    'B079': 'итоговая оценка не только по опросу',
    'B086': 'москвоведам из описи верят те, кто не верит пресс-службе',
    'B088': 'выход техники — следующий предсказуемый повод для волны внимания',
    'B092': 'лечение кошек переходит из расходов компании в бюджет кампании',
    'B093': 'ярмарке не нужно зависеть от площадки партнёра',
}


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
        return source.split(';')[0]
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


def share(v, total):
    return f'{v / total:.1%}'.replace('.', ',')


def summary_tables(b):
    total = int(b.total_rub.sum())
    by_cat = b.groupby('category', sort=False).total_rub.sum().sort_values(ascending=False)
    no_reserve = b[b.category != 'Резерв']
    by_month = no_reserve.groupby('phase', sort=False).total_rub.sum()
    reserve = int(b.loc[b.category == 'Резерв', 'total_rub'].sum())
    cats = table(['Статья', 'Сумма, ₽', 'Доля'], [[c, rub(v), share(v, total)] for c, v in by_cat.items()])
    months = table(['Месяц', 'Сумма, ₽'], [[MONTHS[m], rub(v)] for m, v in by_month.items()]
                   + [['резерв на ноябрь–март', rub(reserve)], ['итого', rub(total)]])
    return total, reserve, cats, months


def line_rows(b):
    b = b.sort_values('phase', key=lambda s: s.map(list(MONTHS).index), kind='stable')
    rows = []
    for r in b.itertuples():
        price = '' if pd.isna(r.unit_cost_rub) else rub(r.unit_cost_rub) if float(r.unit_cost_rub).is_integer() \
            else f'{r.unit_cost_rub:.2f}'.replace('.', ',')
        qty = '' if r.category in TAXES else f'{r.qty:g}'.replace('.', ',')
        month = 'ноябрь–март' if r.category == 'Резерв' else MONTHS[r.phase]
        rows.append([r.line_id, month, r.item.removeprefix('Вариант Б: '), r.unit if r.category not in TAXES else '',
                     price, qty, rub(r.total_rub), basis(r.cost_source, r.category)])
    return table(['№', 'Месяц', 'Статья расходов', 'Единица', 'Цена, ₽', 'Кол-во', 'Сумма, ₽', 'Основание цены'], rows)


COMMON = """Цены услуг указаны без налога на добавленную стоимость (НДС). НДС 22% начисляется раз в месяц на закупки \
месяца, страховые взносы 30% — на оплату труда месяца, резерв — 10% от всех остальных расходов. Резерв не облагается \
НДС: если его потратят на услуги подрядчиков, налог заплатят из него же. Каждая строка округлена до рубля, сумма строк \
равна итогу. Цены взяты из открытых прайсов, закупок и зарплатной статистики Москвы за октябрь 2026 года \
(приложение Е); где открытой цены нет, стоит допущение."""


def budgets():
    a, b = pd.read_csv(BUDGET_A), pd.read_csv(BUDGET_B)
    total_a, reserve_a, cats_a, months_a = summary_tables(a)
    total_b, reserve_b, cats_b, months_b = summary_tables(b)
    strategy = int(a.loc[a.category == STRATEGY, 'total_rub'].sum())
    with_taxes = round(strategy * 1.22 * 1.1)
    team = int(a.loc[a.category.isin(['Оплата труда', 'Страховые взносы']), 'total_rub'].sum())
    nov = int(a.loc[(a.phase == 'Nov 2026') & (a.category != 'Резерв'), 'total_rub'].sum())

    text_a = f"""## Приложение В1. Бюджет, вариант А (с работой консультантов)

Вариант, который требует бриф: в 10 млн входит всё, включая работу консультантов над стратегией. Итог \
{rub(total_a)} ₽, свободно {rub(10_000_000 - total_a)} ₽. Работа консультантов — {rub(strategy)} ₽ без НДС, \
{rub(with_taxes)} ₽ с НДС и резервом; команда кампании из трёх человек со страховыми взносами — {rub(team)} ₽. \
Самый дорогой месяц — ноябрь, {rub(nov)} ₽ без резерва. {COMMON}

По статьям:

{cats_a}

По месяцам (резерв отдельной строкой: он относится ко всей кампании):

{months_a}

Главные допущения:
1. Команда кампании из трёх человек работает с ноября по март, в марте с неполной загрузкой; ставки — по медианам \
зарплатных предложений в Москве. Это исполнители кампании, а не консультанты.
2. Дежурство в новогодние праздники оплачивается не менее чем в двойном размере, как требует Трудовой кодекс.
3. Цена стратегии, схемы по корпусам и страницы проекта — допущения: публичных цен для таких работ нет.
4. Лечение и передержку животных с площадки оплачивает компания из расходов на площадку, в бюджет кампании они не \
входят. Только стерилизация около 50 кошек стоит 100–400 тыс. ₽. Площадку для ярмарки пристройства даёт \
приют-партнёр; если её нет, зал оплачивается из резерва.
5. Право первой заявки на студии для бывших арендаторов — решение заказчика, а не расход кампании.
6. Резерв {rub(reserve_a)} ₽ покрывает непредвиденные расходы: идёт суд, снос виден на фото, цены подрядчиков \
уточняются сметами в ноябре.

Все строки:

{line_rows(a)}
"""
    notes_a = f"""- Данные: `deliverables/budget.csv`, `src/analysis/budget_check.py --vat-rate 0.22 --insurance-rate 0.30 \
--reserve-share 0.10 --write`. Строк {len(a)}, итог {rub(total_a)} ₽.
- Консультанты: строки B000–B002 (категория «{STRATEGY}»). Команда: «Оплата труда» и «Страховые взносы». D-53.
- Ставки: НДС K20, взносы K19, праздничная оплата K18 (T12). Стерилизация: K24. Ярмарка: Codex F8, D-54.
"""
    write('appendix_c_budget.md', 'Приложение В1 — бюджет, вариант А', text_a, notes_a)

    added = b[b['item'].str.startswith('Вариант Б:')]
    groups = [('Заключение независимого эксперта по наследию', ['B080']),
              ('Выставка на ограждении площадки и её обновление', ['B081', 'B082', 'B083', 'B084', 'B085']),
              ('Четыре фокус-группы с жителями', ['B078', 'B079']),
              ('Ролик с москвоведами об описи', ['B086', 'B087']),
              ('Встреча с жителями 04.03 перед выходом техники', ['B088', 'B089', 'B090', 'B091']),
              ('Лечение кошек в бюджете кампании', ['B092']),
              ('Зал для ярмарки пристройства', ['B093'])]
    covered = {i for _, ids in groups for i in ids}
    if set(added.line_id) != covered:
        raise SystemExit(f'variant B lines not grouped: {sorted(set(added.line_id) ^ covered)}')
    rows = []
    for name, ids in groups:
        cost = int(added.loc[added.line_id.isin(ids), 'total_rub'].sum())
        why = next(WHY_B[i] for i in ids if i in WHY_B)
        rows.append([name, rub(cost), why])
    text_b = f"""## Приложение В2. Бюджет, вариант Б (без работы консультантов)

Вариант на случай, если работу консультантов оплачивают отдельно от 10 млн. Из бюджета убраны строки стратегии \
(B000–B002: {rub(strategy)} ₽ без НДС, {rub(with_taxes)} ₽ с НДС и резервом). Освободившиеся деньги идут на шаги, \
которые усиливают слабые места плана. Итог {rub(total_b)} ₽, свободно {rub(10_000_000 - total_b)} ₽. Остальные строки \
совпадают с вариантом А. {COMMON}

Что добавлено (без НДС):

{table(['Что', 'Сумма, ₽', 'Зачем'], rows)}

Сроки и ответственные — шаги R50–R57 в приложении Г.

По статьям:

{cats_b}

По месяцам (резерв отдельной строкой):

{months_b}

Все строки:

{line_rows(b)}
"""
    notes_b = f"""- Данные: `deliverables/budget_variant_b.csv` (тот же пересчёт с `--csv`). Строк {len(b)}, итог {rub(total_b)} ₽.
- Новые цены: `docs/project_facts/prices_variant_b.csv` (K21 фокус-группы, K22 печать на сетке, K23 монтаж, K24
  стерилизация); K03, K12 из T12. Решение о варианте Б: D-53.
"""
    write('appendix_c2_budget_b.md', 'Приложение В2 — бюджет, вариант Б', text_b, notes_b)


def calendar():
    r = pd.read_csv(ROOT / 'deliverables/roadmap.csv')
    rows = []
    for x in r.itertuples():
        code, what = x.activity.split(':', 1)
        rows.append([code, pd.Timestamp(x.week_start).strftime('%d.%m.%y'), what.strip(), x.owner_role,
                     x.deliverable, x.kpi])
    n_b = int((r.status == 'variant_b').sum())
    text = f"""## Приложение Г. Календарь кампании

{len(r)} шагов с 26.10.2026 по 31.03.2027, из них {n_b} только для варианта Б бюджета (помечены «Вариант Б»). \
На каждое согласование у заказчика заложено пять рабочих дней. Официальный новогодний отдых — с 31.12 по 10.01; \
мы допускаем, что у заказчика 11.01 тоже работает только дежурство. Окно проверки ответов 19–26.02 даёт пять \
рабочих дней с учётом рабочей субботы 20.02 (22 и 23.02 — выходные). Диаграмма — рис. Г1, она же отдельным файлом \
appendix_timeline.pdf; полоса показывает срок работы, у разовых шагов — неделю.

[[pagebreak]]
[[figure:reports/figures/fig_gantt.png|Рис. Г1. Календарь кампании по неделям. Цвет — направление работы, пунктир — \
публичные даты, серая полоса — новогодние праздники|15.8]]

{table(['№', 'Неделя', 'Что делаем', 'Кто отвечает', 'Результат', 'Показатель'], rows)}
"""
    notes = """- Данные: `deliverables/roadmap.csv` (R00–R57). Рисунок: `src/report/figure_gantt.py`.
- Производственный календарь 2027: F30 (Минтранс, 18.09.2026). Январский режим заказчика — допущение (Codex F4).
- Новые шаги: D-48 (совет), D-50 (схема), D-51 (животные, встречи, арендаторы), D-53 (вариант Б), D-54 (правки Codex).
"""
    write('appendix_d_calendar.md', 'Приложение Г — календарь', text, notes)


def sections_of(value):
    labels = []
    for part in re.split(r'[;,]', value):
        key = part.strip().lower()
        if key in SECTIONS and SECTIONS[key] not in labels:
            labels.append(SECTIONS[key])
    return labels


def sources():
    f = pd.read_csv(ROOT / 'docs/report_fact_check.csv', dtype=str).fillna('')
    rows = []
    for x in f.itertuples():
        labels = sections_of(x.section)
        if labels and 'основания' not in x.section:
            rows.append([', '.join(labels), x.claim, x.source_url, x.source_date or '—', x.accessed])
    data = [
        ['Интерес публики: запросы «Электрозавод» и «Электрозавод снос», Москва и область, по неделям '
         '30.09.2024–04.10.2026', 'Яндекс Wordstat, https://wordstat.yandex.ru', 'выгрузка 28.10.2026'],
        ['Подписи под открытым письмом: все 19 752 подписи, 25.06–29.10.2026, без имён',
         'https://archi.ru/russia/102373/o-sokhranenii-istoricheskikh-zdanii-elektrozavoda-i-professionalnoe-'
         'obsuzhdenie-proekta-sbor-podpisei', 'снимок 29.10.2026'],
        ['Реакции в соцсетях: 5 905 реакций к публикациям о заводе, июнь–октябрь 2026',
         'YouTube (официальный интерфейс для разработчиков), открытые страницы Telegram, открытые сообщества '
         'ВКонтакте, Дзен', 'сбор 28–29.10.2026'],
        ['Позиции и линии критики: выборка 1 500 реакций, разметка языковой моделью, проверка человеком 120 строк',
         'расчёт консультантов по собранным реакциям', '29.10.2026'],
    ]
    p = pd.concat([pd.read_csv(ROOT / 'workflow/stage1/T12_price_benchmarks/out/prices.csv', dtype=str),
                   pd.read_csv(ROOT / 'docs/project_facts/prices_variant_b.csv', dtype=str)]).fillna('')
    text_costs = ' '.join(pd.concat([pd.read_csv(BUDGET_A), pd.read_csv(BUDGET_B)]).cost_source.fillna(''))
    used = sorted(set(re.findall(r'K\d+', text_costs)), key=lambda k: int(k[1:]))
    prices = []
    for key in used:
        first = p[p.key == key].iloc[0]
        rng = first.price_low_rub if first.price_low_rub == first.price_high_rub else \
            f'{first.price_low_rub}–{first.price_high_rub}'
        prices.append([first.what_priced, f'{rng} ₽' if rng else 'ставка', first.source_url, first.accessed])
    text = f"""## Приложение Е. Источники

Факты отчёта. «Открыто» — дата, когда источник открыли последний раз. Всего исследование опирается на \
{count_sources()} ссылки, полный список хранится в рабочих материалах.

{table(['Раздел', 'Факт', 'Источник', 'Опубликовано', 'Открыто'], rows)}

Данные исследования (числа разделов 1, 3 и 5, приложения А, Б и Д):

{table(['Что', 'Источник', 'Дата'], data)}

Цены бюджета (приложения В1 и В2):

{table(['Что оценено', 'Цена', 'Источник', 'Открыто'], prices)}
"""
    notes = """- Факты: `docs/report_fact_check.csv` (D-45; перепроверка Codex 30.10, D-54). Разделы через «;» разбираются
  по отдельности (Codex F3); строки «основания» и F29 (не используется, D-51) не выводятся.
- Данные: Wordstat — `Tasks_for_humans_exported/`, подписи — D-42, соцсети — `docs/data_cards/`, разметка — D-38, D-46.
- Цены: T12 `prices.csv` и `docs/project_facts/prices_variant_b.csv`, первая строка каждого ключа.
"""
    write('appendix_f_sources.md', 'Приложение Е — источники', text, notes)


def count_sources():
    text = (ROOT / 'docs/sources.md').read_text(encoding='utf-8')
    m = re.search(r'ссылок:\s*(\d+)', text)
    return m.group(1) if m else len(set(re.findall(r'https?://\S+', text)))


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    budgets()
    calendar()
    sources()


if __name__ == '__main__':
    main()
