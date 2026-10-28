"""Build the Dzen rows of the corpus in the schema of corpus_v2.parquet (T17).

Reads only the local raw files data/raw/dzen/2026-10-28/{items,comments}.jsonl.
Writes data/processed/corpus_dzen.parquet, out/corpus_summary_dzen.csv,
out/coverage_dzen.csv and out/build_checks.txt. No network, no new collection.

Run from the repository root:
    .venv/bin/python workflow/stage1/T17_dzen_processing/build_dzen.py
"""
import argparse
import csv
import hashlib
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / 'data/raw/dzen/2026-10-28'
ITEMS = RAW / 'items.jsonl'
COMMENTS = RAW / 'comments.jsonl'
TARGET = ROOT / 'data/processed/corpus_dzen.parquet'
V2_PARQUET = ROOT / 'data/processed/corpus_v2.parquet'
OUT = HERE / 'out'
VERSION = 't17_dzen/1.0'
WINDOW = ('2026-06-01', '2026-10-28')

# Common Russian sentence openers and place/object words that precede a comma but
# are not an addressee. Names are deliberately absent: any other capitalised
# leading word plus comma is treated as a person addressed in the reply.
NOT_AN_ADDRESSEE = set('''
да нет ну жаль вот так наверно наверное давайте поискала зависть каланчевка
москве москва мааадам жк метро из ага ой кстати правда может скорее согласен
согласна ладно хорошо плохо спасибо простите извините думаю конечно однако
значит итак впрочем тоже также кроме главное важно интересно странно похоже
видимо ясно понятно ребята друзья коллеги господа боже господи чёрт черт блин
люди мужики девушки женщина мужчина автор статья завод электрозавод ссср сша
рф рсфср улица дом город этаж квартира питер россия
'''.split())

# A reply may open with a display name or a form of address, optionally wrapped in
# symbols (emoji), then a comma: «Имя,», «Имя Ф.», «Имя Фамилия,», «💜ник,».
ADDRESS = re.compile(
    r"^(?P<pre>[^\w,]{0,12}?)"
    r"(?P<name>[A-Za-zА-ЯЁ][\w.'’\-]*(?:[ \t]+[A-Za-zА-ЯЁ][\w.'’\-]*){0,2})"
    r"(?P<post>[^\w,]{0,12}?),\s*")
WORD = re.compile(r"[A-Za-zА-ЯЁа-яё][\w'’\-]*")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


b = load_module('t11_base', ROOT / 'workflow/stage1/T11_processing/build_corpus.py')
v = load_module('t11_v2', ROOT / 'workflow/stage1/T11_processing/v2/build_corpus_v2.py')
SITE = b.make_site()


def day_of(raw, kind, stats):
    """Raw Dzen dates are calendar days. A missing date stays missing."""
    value = raw.get('published_at')
    if not value:
        stats[kind + '_without_date'] += 1
        return None
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(value)):
        raise ValueError('Unexpected date format in raw ' + kind + ' input')
    return str(value)


def addressee(text):
    """Return the matched display name at the start of a reply, or None."""
    match = ADDRESS.match(text)
    if not match:
        return None
    words = WORD.findall(match.group('name'))
    first = words[0].casefold().replace('ё', 'е')
    if len(first) < 2 or first in NOT_AN_ADDRESSEE:
        return None
    if first in ('user', 'name', 'email', 'phone'):
        return None  # placeholders written by this pipeline or the T16 collector
    return match.group('name')


def mask_addressee(text):
    """Replace a leading addressee with [user], keeping the rest of the text."""
    match = ADDRESS.match(text)
    if not match or not addressee(text):
        return text, 0
    return '[user], ' + text[match.end():], 1


def base(identity, kind, text, collected, day, stats):
    row = dict.fromkeys(v.SCHEMA.names)
    row.update(id=str(identity), platform='dzen', source='dzen', row_type=kind,
               text=text, collected_at=b.utc(collected), published_at=None,
               published_date=day, date_precision='day' if day else 'unknown',
               in_window=bool(day and WINDOW[0] <= day <= WINDOW[1]),
               period=v.period(day), collector_version=VERSION,
               counter_precision='exact_or_null', is_source_owner=None,
               author_id_hash=None, author_type='unknown', matched_keywords=[])
    return row


def post_row(raw, stats):
    day = day_of(raw, 'item', stats)
    text = (raw.get('title') or '') + '\n' + (raw.get('text') or '')
    media = raw.get('author_type')
    display = raw.get('author_display') if media in ('media', 'org') else None
    source_id = display or raw.get('publisher_url_hash')
    row = base(raw['id'], 'post', text, raw['collected_at'], day, stats)
    relevant = bool(SITE.search(text))
    row.update(url=raw.get('url'), source_id=source_id, source_kind=media,
               media_type=raw.get('media_type') or 'text',
               author_id_hash=raw.get('author_id_hash'),
               author_type='org' if media == 'media' else media or 'unknown',
               author_display=display,
               likes=b.number(raw.get('likes')),
               reposts=b.number(raw.get('reposts')),
               comments_count=b.number(raw.get('comments_count')),
               thread_id=str(raw['id']), parent_id=None,
               relevant=relevant,
               relevance_reason='post_mentions' if relevant else 'search_hit_without_term')
    if raw.get('views') is not None:
        stats['item_views_not_carried'] += 1
    return row


def comment_row(raw, post, stats):
    depth = raw.get('depth')
    if depth not in (0, 1):
        raise ValueError('Unexpected comment depth in raw input')
    day = day_of(raw, 'comment', stats)
    item_id = str(raw['thread_id'])
    row = base(raw['id'], 'comment' if depth == 0 else 'reply',
               raw.get('text') or '', raw['collected_at'], day, stats)
    if depth == 0:
        parent_id = item_id
    else:
        root = raw.get('parent_id')
        if not isinstance(root, int):
            raise ValueError('Reply parent is not a root number in raw input')
        parent_id = f'{item_id}-root{root}'
    row.update(url=raw.get('url'), source_id=post['source_id'],
               source_kind=post['source_kind'], media_type='text',
               author_id_hash=raw.get('author_id_hash'),
               author_type='person' if raw.get('author_type') == 'person' else 'unknown',
               author_display=None, likes=b.number(raw.get('likes')),
               reposts=None, comments_count=None,
               thread_id=item_id, parent_id=parent_id,
               relevant=post['relevant'], relevance_reason='thread_context')
    return row


def build(stats, drops):
    snapshots = {}
    items = list(b.load_rows([ITEMS], snapshots))
    comments = list(b.load_rows([COMMENTS], snapshots))
    stats['raw_items'], stats['raw_comments'] = len(items), len(comments)

    posts, seen = {}, set()
    for raw in items:
        identity = str(raw['id'])
        if identity in seen:
            drops.append((identity, 'duplicate_item_id'))
            stats['dropped_duplicate_item'] += 1
            continue
        seen.add(identity)
        posts[identity] = post_row(raw, stats)

    rows, ids = list(posts.values()), set(posts)
    for raw in comments:
        identity = str(raw['id'])
        if identity in ids:
            drops.append((identity, 'duplicate_comment_id'))
            stats['dropped_duplicate_comment'] += 1
            continue
        post = posts.get(str(raw.get('thread_id')))
        if post is None:
            drops.append((identity, 'thread_item_absent'))
            stats['dropped_comment_without_item'] += 1
            continue
        ids.add(identity)
        rows.append(comment_row(raw, post, stats))

    keys = {r['id'] for r in rows}
    for row in rows:
        original = row['text']
        row['matched_keywords'] = sorted({m.group(0).casefold()
                                          for rx in (SITE, b.TOPIC)
                                          for m in rx.finditer(original)})
        text = original
        if row['row_type'] == 'reply':
            text, replaced = mask_addressee(text)
            stats['addressee_prefixes_replaced'] += replaced
            stats['reply_rows_with_addressee'] += bool(replaced)
        row['text'] = b.mask(text, None)
        row['author_display'] = b.mask(row['author_display'], None)
        row['lang'] = b.language(row['text'])
        stats['rows_with_changed_text'] += row['text'] != original
        row['parent_present'] = row['parent_id'] is None or row['parent_id'] in keys
        row['thread_present'] = row['thread_id'] is None or row['thread_id'] in keys
        row['context_complete'] = row['parent_present'] and row['thread_present']
    for row in rows:
        parent = next((r for r in rows if r['id'] == row['parent_id']), None) if row['parent_id'] else None
        if row['context_complete'] and parent is not None and not parent['context_complete']:
            row['context_complete'] = False
    rows.sort(key=lambda r: r['id'])
    return rows, snapshots


def coverage(rows):
    reactions = [r for r in rows if r['row_type'] in ('comment', 'reply')]
    broad = [r for r in reactions if r['in_window'] and r['relevant']]
    eligible = [r for r in broad if r['context_complete']]
    p3 = [r for r in reactions if r['period'] == 'P3']
    counts = Counter(r['thread_id'] for r in p3)
    largest = counts.most_common(1)[0][1] if counts else 0
    top3 = sum(n for _, n in counts.most_common(3))
    return dict(platform='dzen', all_rows=len(rows),
                publications=sum(r['row_type'] in ('post', 'video') for r in rows),
                reactions=len(reactions), broad_p3=len(broad),
                strict_complete_p3=len(eligible),
                strict_context_excluded=sum(r['relevant'] and not r['context_complete']
                                            for r in broad),
                unique_authors=len({r['author_id_hash'] for r in eligible
                                    if r['author_id_hash']}),
                unknown_author_rows=sum(not r['author_id_hash'] for r in eligible),
                day_precision=sum(r['date_precision'] == 'day' for r in rows),
                p3_largest_item_share=round(100 * largest / len(p3), 2) if p3 else None,
                p3_top3_items_share=round(100 * top3 / len(p3), 2) if p3 else None)


def self_tests(rows, tables, stats, snapshots):
    checks = []

    def check(name, passed):
        checks.append((name, bool(passed)))

    ids = [r['id'] for r in rows]
    keys = set(ids)
    check('schema_equal_to_corpus_v2', tables['schema'])
    check('pandas_concat_with_corpus_v2', tables['concat'])
    check('unique_ids', len(keys) == len(ids))
    check('parents_exist', all(r['parent_id'] is None or r['parent_id'] in keys for r in rows))
    check('threads_exist', all(r['thread_id'] is None or r['thread_id'] in keys for r in rows))
    check('context_complete_all_rows', all(r['context_complete'] for r in rows))
    check('no_published_at_without_time',
          all(r['published_at'] is None for r in rows if r['date_precision'] in ('day', 'unknown')))
    check('day_rows_keep_day',
          all(r['published_date'] and r['date_precision'] == 'day'
              for r in rows if r['published_date']))
    check('in_window_from_day',
          all(r['in_window'] == (bool(r['published_date']) and WINDOW[0] <= r['published_date'] <= WINDOW[1])
              for r in rows))
    check('period_from_day', all(r['period'] == v.period(r['published_date']) for r in rows))
    check('no_unmasked_contact',
          not any(b.EMAIL.search(r['text']) or b.HANDLE.search(r['text']) or b.PHONE.search(r['text'])
                  for r in rows))
    check('no_addressee_left_at_reply_start',
          all(addressee(r['text']) is None for r in rows if r['row_type'] == 'reply'))
    check('display_names_only_for_posts',
          all(r['author_display'] is None for r in rows if r['row_type'] in ('comment', 'reply'))
          and all(r['author_display'] is None for r in rows
                  if r['row_type'] == 'post' and r['author_type'] not in ('org', 'media')))
    check('counters_integer_or_null',
          all(r[k] is None or (isinstance(r[k], int) and r[k] >= 0)
              for r in rows for k in ('views', 'likes', 'reposts', 'comments_count')))
    check('views_not_carried', all(r['views'] is None for r in rows))
    check('raw_item_count', stats['raw_items'] == 22)
    check('raw_comment_count', stats['raw_comments'] == 987)
    check('output_rows_match_raw',
          len(rows) == stats['raw_items'] - stats['dropped_duplicate_item']
          + stats['raw_comments'] - stats['dropped_duplicate_comment']
          - stats['dropped_comment_without_item'])
    check('raw_inputs_unchanged',
          all(hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in snapshots.items()))
    return checks


def main():
    parser = argparse.ArgumentParser(
        description='Build Dzen rows in the corpus_v2 schema and its summary tables.')
    parser.parse_args()
    stats, drops = Counter(), []
    for name in ('dropped_duplicate_item', 'dropped_duplicate_comment',
                 'dropped_comment_without_item', 'dropped_rows'):
        stats[name] = 0
    rows, snapshots = build(stats, drops)
    stats['output_rows'] = len(rows)
    stats['output_posts'] = sum(r['row_type'] == 'post' for r in rows)
    stats['output_comments'] = sum(r['row_type'] == 'comment' for r in rows)
    stats['output_replies'] = sum(r['row_type'] == 'reply' for r in rows)
    stats['dropped_rows'] = len(drops)

    table = pa.Table.from_pylist(rows, schema=v.SCHEMA)
    import pandas as pd
    v2 = pq.read_table(V2_PARQUET)
    concat = pd.concat([v2.to_pandas(), table.to_pandas()], ignore_index=True)
    tables = {
        'schema': table.schema.equals(pq.read_schema(V2_PARQUET)),
        'concat': len(concat) == v2.num_rows + table.num_rows
                  and list(concat.columns) == list(v2.schema.names),
    }
    checks = self_tests(rows, tables, stats, snapshots)
    report = ['T17 Dzen: local processing into the corpus_v2 schema. No texts in this report.']
    report += [f'{k}={stats[k]}' for k in sorted(stats)]
    report += [f'dropped={identity}:{reason}' for identity, reason in drops]
    report += [('PASS ' if passed else 'FAIL ') + name for name, passed in checks]

    if not all(passed for _, passed in checks):
        OUT.mkdir(exist_ok=True)
        report.append('FAIL: parquet and summaries not written.')
        (OUT / 'build_checks.txt').write_text('\n'.join(report) + '\n')
        print('\n'.join(report))
        return 1

    OUT.mkdir(exist_ok=True)
    target = TARGET
    tmp = target.with_suffix('.tmp')
    pq.write_table(table, tmp, compression='zstd')
    if not pq.read_table(tmp).equals(table):
        raise ValueError('Parquet read-back differs from the in-memory table')
    tmp.replace(target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()

    with (OUT / 'corpus_summary_dzen.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=b.SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(b.summary(rows))
    cov = coverage(rows)
    with (OUT / 'coverage_dzen.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cov))
        writer.writeheader()
        writer.writerow(cov)

    report += [f'input_sha256={p.name}:{digest}' for p, digest in sorted(snapshots.items())]
    report.append('parquet_sha256=' + digest)
    report.append('PASS parquet_read_back')
    report.append('PASS all_checks')
    (OUT / 'build_checks.txt').write_text('\n'.join(report) + '\n')
    print('\n'.join(report))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as exc:
        OUT.mkdir(exist_ok=True)
        failure = ('FAIL: invalid input or IO error, outputs are not a completed run. '
                   + type(exc).__name__)
        (OUT / 'build_checks.txt').write_text(failure + '\n')
        print(failure, file=sys.stderr)
        raise SystemExit(1)
