"""Build the T11 pseudonymised corpus from completed local raw files (no network).

Run from the repository root. Default processes YouTube and any non-pilot Telegram
files in the latest date directory. Use --platforms youtube for the first batch.
Only card outputs are replaced; raw files, the salt and source configuration are read-only.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

CARD = Path(__file__).resolve().parent
ROOT = CARD.parents[2]
VERSION = 't11/1.0'
START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 10, 29, tzinfo=timezone.utc)  # exclusive
STEMS = ('снос', 'снес', 'демонтаж', 'эталон', 'фасад', 'наслед', 'памятник', 'башн', 'шухов', 'завод')
TOPIC = re.compile(r'\b(?:' + '|'.join(STEMS) + r')\w*', re.I)
HANDLE = re.compile(r'(?<!\w)@[\w.\-]+', re.U)
EMAIL = re.compile(r'(?<![\w.+-])[\w.+-]+@[\w.-]+\.[\w-]+', re.U)
PHONE = re.compile(r'(?<!\w)\+?\d(?:[\s().-]*\d){9,14}(?!\w)')
FIELDS = [
 ('id', pa.string()), ('source', pa.string()), ('url', pa.string()),
 ('parent_id', pa.string()), ('thread_id', pa.string()),
 ('author_id_hash', pa.string()), ('author_type', pa.string()), ('author_display', pa.string()),
 ('published_at', pa.string()), ('collected_at', pa.string()), ('text', pa.string()),
 ('lang', pa.string()), ('media_type', pa.string()), ('views', pa.int64()),
 ('likes', pa.int64()), ('reposts', pa.int64()), ('comments_count', pa.int64()),
 ('matched_keywords', pa.list_(pa.string())), ('collector_version', pa.string()),
 ('platform', pa.string()), ('row_type', pa.string()), ('source_id', pa.string()),
 ('source_kind', pa.string()), ('is_source_owner', pa.bool_()), ('relevant', pa.bool_()),
 ('relevance_reason', pa.string()), ('in_window', pa.bool_()),
]
SCHEMA = pa.schema(FIELDS)
SUMMARY_FIELDS = ['summary_type', 'platform', 'source_kind', 'row_type', 'relevant',
                  'relevance_reason', 'in_window', 'row_count', 'unique_authors']


def utc(value):
    if not value:
        return None
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timestamp without timezone in raw input')
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def number(value):
    if value is None or value == '':
        return None
    # Rounded Telegram view strings (K/M) are unknown, never invented integers.
    if isinstance(value, int) or re.fullmatch(r'\d+', str(value)):
        return int(value)
    return None


def language(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 'empty'
    cyr = sum('\u0400' <= c <= '\u052f' for c in letters)
    return 'ru' if cyr * 2 >= len(letters) else 'other'


def load_rows(paths, snapshots):
    for path in paths:
        blob = path.read_bytes()
        snapshots[path] = hashlib.sha256(blob).hexdigest()
        for lineno, line in enumerate(blob.decode('utf-8').splitlines(), 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except ValueError:
                    raise ValueError(f'Invalid JSONL: {path.name}, line {lineno}') from None


def complete_files(base, prefix):
    return sorted(p for p in base.glob(prefix + '_*.jsonl')
                  if not any(mark in p.name for mark in ('_pilot', '_partial')))


def latest(records, key, stats, category):
    result = {}
    for record in records:
        identity = key(record)
        if identity in result:
            stats['duplicates_' + category] += 1
            old = result[identity]
            if (utc(record.get('_collected_at')) or '') < (utc(old.get('_collected_at')) or ''):
                continue
        result[identity] = record
    return result


def make_site():
    variants = yaml.safe_load((ROOT / 'workflow/stage0/T06_keyword_variants/out/variants.yaml').read_text())
    forms = next(v['case_forms'] for v in variants if v['term'] == 'Электрозавод')
    return re.compile(r'\b(?:' + '|'.join(re.escape(f) for f in forms) + r')\b', re.I)


def base_row(platform, identity, kind, source_id, source_kind, text, published, collected):
    published, collected = utc(published), utc(collected)
    if published is None or collected is None:
        raise ValueError('Missing publication or collection timestamp; cannot satisfy T11')
    row = dict.fromkeys(SCHEMA.names)
    row.update(id=str(identity), source=platform, platform=platform, row_type=kind,
               source_id=source_id, source_kind=source_kind, text=text or '',
               published_at=published, collected_at=collected, author_type='unknown',
               collector_version=VERSION, is_source_owner=False, matched_keywords=[],
               in_window=START <= datetime.fromisoformat(published.replace('Z', '+00:00')) < END)
    return row


def author_hash(salt, platform, raw_id):
    if not raw_id:
        return None
    return hashlib.sha256(salt + (platform + ':' + str(raw_id)).encode()).hexdigest()[:16]


def youtube(site, salt, stats, snapshots, private):
    base = ROOT / 'data/raw/youtube/2026-10-28'
    video_files = complete_files(base, 'videos')
    comment_files = complete_files(base, 'comments')
    stats['youtube_video_files'] = len(video_files)
    stats['youtube_comment_files'] = len(comment_files)
    vids = latest(load_rows(video_files, snapshots), lambda x: x['id'], stats, 'video')
    stats['youtube_unique_candidate_videos'] = len(vids)
    included = {i: v for i, v in vids.items() if site.search(v['snippet']['title'] + '\n' + v['snippet'].get('description', ''))}
    stats['youtube_excluded_videos_no_site_form'] = len(vids) - len(included)
    rows, owner = [], {}
    for identity, video in sorted(included.items()):
        sn = video['snippet']
        kind = 'topical' if site.search(sn['title']) else 'digest'
        owner[identity] = sn.get('channelId')
        row = base_row('youtube', identity, 'video', identity, kind,
                       sn['title'] + '\n' + sn.get('description', ''), sn['publishedAt'], video['_collected_at'])
        row.update(url='https://www.youtube.com/watch?v=' + identity, media_type='video',
                   author_id_hash=author_hash(salt, 'youtube', sn.get('channelId')),
                   author_display=sn.get('channelTitle'), relevant=True,
                   relevance_reason='topical_source' if kind == 'topical' else 'digest_source')
        for target, field in [('views','viewCount'), ('likes','likeCount'), ('comments_count','commentCount')]:
            row[target] = number(video.get('statistics', {}).get(field))
        rows.append(row)
    stats['youtube_included_videos'] = len(included)
    messages = []
    raw_ids = {'comment': set(), 'reply': set()}
    for thread in load_rows(comment_files, snapshots):
        video_id = thread['snippet']['videoId']
        top = thread['snippet']['topLevelComment']
        children = [top] + thread.get('replies', {}).get('comments', [])
        for comment in children:
            sn = comment['snippet']
            for field in ('authorDisplayName', 'authorChannelUrl', 'authorProfileImageUrl'):
                if sn.get(field):
                    private.add(sn[field])
            raw_id = sn.get('authorChannelId', {}).get('value')
            if raw_id:
                private.add(raw_id)
        if video_id not in included:
            stats['youtube_excluded_top_level'] += 1
            stats['youtube_excluded_replies'] += len(children) - 1
            continue
        stats['youtube_raw_top_level'] += 1
        stats['youtube_raw_replies'] += len(children) - 1
        if thread['snippet'].get('totalReplyCount') != len(children) - 1:
            stats['youtube_threads_reply_count_mismatch'] += 1
        for index, comment in enumerate(children):
            raw_ids['comment' if index == 0 else 'reply'].add(comment['id'])
            messages.append({'comment': comment, 'video': video_id, 'top': top['id'],
                             'kind': 'comment' if index == 0 else 'reply',
                             'reply_count': thread['snippet'].get('totalReplyCount') if index == 0 else None,
                             '_collected_at': thread['_collected_at']})
    messages = latest(messages, lambda x: x['comment']['id'], stats, 'youtube_message')
    mentions = defaultdict(bool)
    for m in messages.values():
        sn = m['comment']['snippet']
        text = sn.get('textOriginal', sn.get('textDisplay', ''))
        mentions[(m['video'], m['top'])] |= bool(site.search(text) or TOPIC.search(text))
    for identity, m in sorted(messages.items()):
        sn = m['comment']['snippet']
        text = sn.get('textOriginal', sn.get('textDisplay', ''))
        video_id = m['video']
        source_kind = 'topical' if site.search(included[video_id]['snippet']['title']) else 'digest'
        relevant = source_kind == 'topical' or mentions[(video_id, m['top'])]
        raw_id = sn.get('authorChannelId', {}).get('value')
        row = base_row('youtube', identity, m['kind'], video_id, source_kind,
                       text, sn['publishedAt'], m['_collected_at'])
        row.update(url=f'https://www.youtube.com/watch?v={video_id}&lc={identity}',
                   parent_id=video_id if m['kind'] == 'comment' else m['top'], thread_id=m['top'],
                   author_id_hash=author_hash(salt, 'youtube', raw_id),
                   is_source_owner=bool(raw_id and raw_id == owner[video_id]), media_type='text',
                   likes=number(sn.get('likeCount')), comments_count=number(m['reply_count']), relevant=relevant,
                   relevance_reason=('topical_source' if source_kind == 'topical' else
                                     'thread_mentions' if relevant else 'off_topic_digest'))
        rows.append(row)
    stats['youtube_output_top_level'] = sum(r['row_type'] == 'comment' for r in rows)
    stats['youtube_output_replies'] = sum(r['row_type'] == 'reply' for r in rows)
    stats['youtube_unique_raw_messages'] = len(messages)
    stats['youtube_unique_raw_top_level'] = len(raw_ids['comment'])
    stats['youtube_unique_raw_replies'] = len(raw_ids['reply'])
    stats['youtube_duplicate_top_level'] = stats['youtube_raw_top_level'] - stats['youtube_output_top_level']
    stats['youtube_duplicate_replies'] = stats['youtube_raw_replies'] - stats['youtube_output_replies']
    return rows


def telegram(site, salt, stats, snapshots):
    dirs = sorted(p for p in (ROOT / 'data/raw/telegram').glob('*') if p.is_dir() and re.fullmatch(r'\d{4}-\d{2}-\d{2}', p.name))
    if not dirs:
        stats['telegram_pending_full_collection'] = 1
        return []
    base = dirs[-1]
    posts_files, comment_files = complete_files(base, 'posts'), complete_files(base, 'comments')
    if not posts_files:
        stats['telegram_pending_full_collection'] = 1
        return []
    stats['telegram_post_files'], stats['telegram_comment_files'] = len(posts_files), len(comment_files)
    with (ROOT / 'workflow/stage0/T01_telegram_video/out/telegram.csv').open() as stream:
        channels = {r['handle'].lower(): r for r in csv.DictReader(stream)}
    posts = latest(load_rows(posts_files, snapshots), lambda p: (p['channel'].lower(), str(p['id'])), stats, 'telegram_post')
    rows, post_rows = [], {}
    declared_loaded = {}
    for (channel, pid), post in sorted(posts.items()):
        row = base_row('telegram', f'{channel}:post:{pid}', 'post', channel,
                       channels.get(channel, {}).get('owner_type', 'unknown'),
                       post.get('text', ''), post['published_at'], post['_collected_at'])
        if post.get('comments_loaded') is not None:
            declared_loaded[(channel, pid)] = int(post['comments_loaded'])
        stats['telegram_comments_status_' + str(post.get('comments_status', 'unknown'))] += 1
        row.update(url=post.get('url'), thread_id=row['id'], is_source_owner=None,
                   author_id_hash=author_hash(salt, 'telegram', channel),
                   author_display=channels.get(channel, {}).get('title'),
                   relevant=bool(site.search(row['text'])),
                   relevance_reason='post_mentions' if site.search(row['text']) else 'search_hit_without_term',
                   media_type='mixed' if post.get('media') else 'text', views=number(post.get('views')))
        if post.get('views') and row['views'] is None:
            stats['telegram_rounded_or_unknown_views_to_null'] += 1
        post_rows[(channel, pid)] = row
        rows.append(row)
    comments = latest(load_rows(comment_files, snapshots),
                      lambda c: (c['channel'].lower(), str(c['post_id']), str(c['id'])), stats, 'telegram_comment')
    actual_loaded = Counter((channel, pid) for channel, pid, cid in comments)
    stats['telegram_declared_loaded_mismatch'] = sum(actual_loaded[key] != n for key,n in declared_loaded.items())
    stats['telegram_missing_reply_parents'] = sum(c.get('reply_to') is not None and (channel, pid, str(c['reply_to'])) not in comments for (channel,pid,cid),c in comments.items())
    for (channel, pid, cid), comment in sorted(comments.items()):
        parent = post_rows.get((channel, pid))
        if parent is None:
            raise ValueError('Telegram comment has no loaded post; rerun after collection finishes')
        row = base_row('telegram', f'{channel}:post:{pid}:comment:{cid}', 'comment', channel,
                       parent['source_kind'], comment.get('text', ''), comment['published_at'], comment['_collected_at'])
        target = comment.get('reply_to')
        row.update(url=comment.get('url'), thread_id=parent['id'],
                   parent_id=f'{channel}:post:{pid}:comment:{target}' if target is not None else parent['id'],
                   author_id_hash=comment.get('sender_hash') or None, is_source_owner=None, relevant=parent['relevant'],
                   relevance_reason='thread_context', media_type='text')
        rows.append(row)
    return rows


def mask(text, forbidden):
    if text is None:
        return None
    if forbidden:
        text = forbidden.sub('[user]', text)
    text = EMAIL.sub('[email]', text)
    text = HANDLE.sub('[user]', text)
    return PHONE.sub('[phone]', text)


def self_tests(rows, site, stats, forbidden):
    checks = []
    def check(name, passed):
        checks.append((name, bool(passed)))
    keys = {(r['platform'], r['id']) for r in rows}
    check('unique_platform_id', len(keys) == len(rows))
    check('parent_integrity', all(r['parent_id'] is None or (r['platform'], r['parent_id']) in keys for r in rows))
    check('telegram_loaded_counts', stats['telegram_declared_loaded_mismatch'] == 0)
    check('thread_integrity', all(r['thread_id'] is None or (r['platform'], r['thread_id']) in keys for r in rows))
    check('youtube_unique_top_and_reply_totals', stats['youtube_output_top_level'] == stats['youtube_unique_raw_top_level'] and stats['youtube_output_replies'] == stats['youtube_unique_raw_replies'])
    check('youtube_unique_raw_totals', stats['youtube_output_top_level'] + stats['youtube_output_replies'] == stats['youtube_unique_raw_messages'])
    check('youtube_raw_minus_deduplicated', stats['youtube_raw_top_level'] + stats['youtube_raw_replies'] - stats['duplicates_youtube_message'] == stats['youtube_unique_raw_messages'])
    check('publication_and_collection_utc', all(r['published_at'].endswith('Z') and r['collected_at'].endswith('Z') for r in rows))
    check('window_flags', all(r['in_window'] == (START <= datetime.fromisoformat(r['published_at'].replace('Z','+00:00')) < END) for r in rows))
    check('no_commenter_display_names', all(r['author_display'] is None for r in rows if r['row_type'] in ('comment','reply')))
    check('no_raw_author_values', forbidden is None or all(not forbidden.search(str(v)) for r in rows for v in r.values() if v is not None))
    check('masked_contacts', all(not (EMAIL.search(r['text']) or HANDLE.search(r['text']) or PHONE.search(r['text'])) for r in rows))
    check('null_for_unavailable_metrics', all(r[k] is None or (isinstance(r[k], int) and r[k] >= 0) for r in rows for k in ('views','likes','reposts','comments_count')))
    check('site_positive_forms', all(site.search(x) for x in ('Электрозавод', 'ЭЛЕКТРОЗАВОДА', 'об Электрозаводе')))
    check('site_negative_boundaries', all(not site.search(x) for x in ('Электрозаводская','Электрозаводской','Электрозаводск','Электрозаводы','суперЭлектрозавод')))
    check('language_examples', language('Завод test') == 'ru' and language('hello') == 'other' and language('123!?') == 'empty')
    check('contact_examples', mask('Пишите @sample_user или test@example.org +7 (999) 123-45-67', None) == 'Пишите [user] или [email] [phone]')
    check('topic_stem_boundaries', bool(TOPIC.search('снесут')) and not TOPIC.search('переснос'))
    return checks


def summary(rows):
    groups = defaultdict(list)
    for r in rows:
        key = tuple(r[k] for k in ('platform','source_kind','row_type','relevant','relevance_reason','in_window'))
        groups[key].append(r)
    result = []
    for key, members in sorted(groups.items()):
        item = dict(zip(SUMMARY_FIELDS[1:7], key))
        item.update(summary_type='group', row_count=len(members),
                    unique_authors=len({r['author_id_hash'] for r in members if r['author_id_hash']}))
        result.append(item)
    for platform in sorted({r['platform'] for r in rows}):
        members = [r for r in rows if r['platform'] == platform]
        result.append(dict(summary_type='platform_authors', platform=platform, row_count=len(members),
                           unique_authors=len({r['author_id_hash'] for r in members if r['author_id_hash']})))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platforms', nargs='+', choices=['youtube','telegram'], default=['youtube','telegram'])
    args = parser.parse_args()
    # read_bytes intentionally preserves the exact secret, including any trailing newline.
    salt = (ROOT / '.secrets/hash_salt').read_bytes()
    if not salt:
        raise ValueError('Empty hash salt')
    site, stats, snapshots, private = make_site(), Counter(), {}, set()
    rows = []
    if 'youtube' in args.platforms:
        rows.extend(youtube(site, salt, stats, snapshots, private))
    if 'telegram' in args.platforms:
        rows.extend(telegram(site, salt, stats, snapshots))
    forbidden = re.compile('|'.join(re.escape(v) for v in sorted(private, key=lambda v: (-len(v), v)))) if private else None
    for row in rows:
        original = row['text']
        row['matched_keywords'] = sorted(set(m.group(0).casefold() for rx in (site, TOPIC) for m in rx.finditer(original)))
        row['text'] = mask(original, forbidden)
        row['author_display'] = mask(row['author_display'], forbidden)
        row['lang'] = language(row['text'])
        if original != row['text']:
            stats['rows_with_masked_text'] += 1
    rows.sort(key=lambda r: (r['platform'], r['id']))
    checks = self_tests(rows, site, stats, forbidden)
    unchanged = all(hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in snapshots.items())
    checks.append(('raw_snapshot_unchanged_during_build', unchanged))
    report = ['T11: локальная обработка; тексты и личности в отчёт не включены.',
              'platforms=' + ','.join(sorted(set(args.platforms))),
              'pyarrow=' + pa.__version__,
              'window=2026-06-01T00:00:00Z / 2026-10-29T00:00:00Z (exclusive)',
              'input_files=' + str(len(snapshots))]
    report.extend(f'{k}={v}' for k,v in sorted(stats.items()))
    report.extend(('PASS' if passed else 'FAIL') + ' ' + name for name,passed in checks)
    report.append('output_rows=' + str(len(rows)))
    out = CARD / 'out'
    out.mkdir(exist_ok=True)
    if not all(passed for _,passed in checks):
        report.append('FAIL: parquet и summary не изменены.')
        (out / 'test_report.txt').write_text('\n'.join(report) + '\n')
        print('\n'.join(report))
        return 1
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    target = ROOT / 'data/processed/corpus.parquet'
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix('.parquet.tmp')
    pq.write_table(table, temp, compression='zstd', version='2.6')
    readback = pq.read_table(temp)
    if not table.equals(readback):
        raise ValueError('Parquet read-back differs from in-memory table')
    temp.replace(target)
    with (out / 'corpus_summary.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary(rows))
    report += ['PASS parquet_read_back', 'PASS all_checks',
               'Ограничение: relevant обозначает правило отбора T11, а не проверенную позицию автора.']
    (out / 'test_report.txt').write_text('\n'.join(report) + '\n')
    print('\n'.join(report))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as exc:
        # Do not expose arbitrary raw values in an exception traceback.
        failure = 'FAIL: invalid/missing input or IO error; outputs are not a completed new run. ' + type(exc).__name__
        (CARD / 'out').mkdir(exist_ok=True)
        (CARD / 'out/test_report.txt').write_text(failure + '\n')
        print(failure, file=sys.stderr)
        raise SystemExit(1)
