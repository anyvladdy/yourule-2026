"""Build docs/sources.md: every URL the project relies on, with the date it was opened (AGENTS §7).

Run from the repository root: .venv/bin/python src/report/sources.py
Reads the integrated tables in docs/ and the accepted worker outputs that have no integrated copy, plus the URLs in
the markdown notes that feed the report. A URL listed several times keeps every place it is used and its latest
`accessed` date. URLs from markdown carry the date stated in that note, or none; the final fact check of the report
opens again every source the report cites and fills missing dates. Outlets designated undesirable (R12) are marked.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# (file, id column, url columns, short label for the "used in" list)
TABLES = [
    ('docs/project_facts/timeline.csv', 'date', ['source_url'], 'хронология'),
    ('docs/project_facts/reality_check.csv', 'claim_id', ['source_url'], 'проверка брифа'),
    ('docs/project_facts/developer_statements.csv', 'stmt_id', ['url'], 'заявления компании'),
    ('docs/project_facts/official.csv', 'doc_id', ['url'], 'официальные документы'),
    ('workflow/stage0/T01_telegram_video/out/telegram.csv', 'handle', ['url', 'relevant_post_url'], 'T01 Telegram'),
    ('workflow/stage0/T01_telegram_video/out/video.csv', 'title', ['url'], 'T01 видео'),
    ('workflow/stage0/T02_vk_petitions/out/petitions.csv', 'pet_id', ['url'], 'петиции'),
    ('workflow/stage0/T03_media/out/articles.csv', 'art_id', ['url'], 'СМИ'),
    ('workflow/stage1/T12_price_benchmarks/out/prices.csv', 'key', ['source_url'], 'цены'),
    ('workflow/stage1/T13_district_voices/out/chats.csv', 'name', ['url', 'evidence_url'], 'T13 чаты'),
    ('workflow/stage1/T13_district_voices/out/newspapers.csv', 'paper', ['url'], 'T13 газеты'),
    ('workflow/stage1/T14_tenants_deputies/out/statements.csv', 'actor', ['url'], 'T14 высказывания'),
    ('docs/report_fact_check.csv', 'fact_id', ['source_url'], 'проверка фактов отчёта'),
    ('docs/project_facts/prices_variant_b.csv', 'key', ['source_url'], 'цены варианта Б'),
]
NOTES = ['docs/audiences.md', 'docs/etalon_channels.md', 'docs/analog_cases.md', 'docs/decisions.md',
         'deliverables/budget.csv']
URL = re.compile(r'https?://[^\s)>|`"\'«»,;]+')
DATE = re.compile(r'20\d\d-\d\d-\d\d')
UNDESIRABLE = ('meduza.io',)


def main():
    used, accessed = defaultdict(set), defaultdict(str)
    for path, id_column, url_columns, label in TABLES:
        with open(ROOT / path, encoding='utf-8') as stream:
            for row in csv.DictReader(stream):
                for column in url_columns:
                    url = (row.get(column) or '').strip()
                    if not url.startswith('http'):
                        continue
                    used[url].add(f'{label} {row.get(id_column, "")[:40]}'.strip())
                    accessed[url] = max(accessed[url], (row.get('accessed') or '').strip())
    for path in NOTES:
        for line in (ROOT / path).read_text(encoding='utf-8').splitlines():
            dates = DATE.findall(line)
            for url in URL.findall(line):
                url = url.rstrip('.')
                used[url].add(Path(path).name)
                # a date in the same line is the opening date only when the line says so
                if 'accessed' in line and dates:
                    accessed[url] = max(accessed[url], max(dates))
    lines = ['# Источники', '',
             'Для кого: люди и агенты, которые пишут и проверяют отчёт. Зачем: у каждого факта отчёта есть ссылка и дата,',
             'когда её открыли (AGENTS §7). Собрано скриптом `src/report/sources.py`, вручную не править.',
             'Пустая дата: ссылка взята из заметки без даты открытия; перед цитированием открыть заново.',
             'Отметка R12: издание признано нежелательным в России; в отчёте не цитируется.', '',
             f'Всего ссылок: {len(used)}; с датой открытия: {sum(1 for u in used if accessed[u])}.', '',
             '| URL | Открыт | Где используется |', '|---|---|---|']
    for url in sorted(used):
        mark = ' (R12)' if any(domain in url for domain in UNDESIRABLE) else ''
        lines.append(f'| {url}{mark} | {accessed[url]} | {"; ".join(sorted(used[url]))[:160]} |')
    (ROOT / 'docs/sources.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'docs/sources.md: {len(used)} URLs, {sum(1 for u in used if accessed[u])} with an accessed date')


if __name__ == '__main__':
    main()
