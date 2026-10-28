"""Collect posts about Электрозавод from public Telegram channels and their comments, without login (D-21).

Adapted from the user's stage2_selenium parser. Run from the repository root.
Posts: channel search t.me/s/<channel>?q=<term> through requests.
Comments: discussion widget t.me/<channel>/<post>?embed=1&discussion=1 in headless Chrome (Selenium).
Reader pace: random pauses before every page. HTTP 429 stops the whole run; it is not worked around.
Comment authors are stored only as a salted hash (salt in .secrets/hash_salt, not in git). A forward keeps
the source link only when it points to a channel post; forwards from people are stored as person_or_hidden.

Output in data/raw/telegram/<YYYY-MM-DD>/: posts_<channel>.jsonl, comments_<channel>.jsonl, _run.json.
A channel whose posts file already exists is skipped, so an interrupted run can be restarted.
"""
import argparse
import csv
import hashlib
import json
import random
import re
import secrets
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

VERSION = 'telegram_web/0.1'
ROOT = Path(__file__).resolve().parents[2]
T01_CHANNELS = ROOT / 'workflow/stage0/T01_telegram_video/out/telegram.csv'
# Channel search matches word forms: in the pilot all case forms of Электрозавод returned the same 22 posts.
DEFAULT_TERMS = ['Электрозавод', 'Система Сити']
HEADERS = {'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'}
MEDIA = {'photo': '.tgme_widget_message_photo_wrap', 'video': '.tgme_widget_message_video_player',
         'document': '.tgme_widget_message_document_wrap', 'audio': '.tgme_widget_message_audio',
         'voice': '.tgme_widget_message_voice', 'poll': '.tgme_widget_message_poll'}


class Stop(Exception):
    """Telegram asked us to slow down or showed a wall: stop and ask the user."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def pause(low=2.0, high=5.0):
    time.sleep(random.uniform(low, high))


def salt():
    path = ROOT / '.secrets' / 'hash_salt'
    if not path.exists():
        path.parent.mkdir(exist_ok=True)
        path.write_text(secrets.token_hex(32), encoding='utf-8')
    return path.read_text(encoding='utf-8').strip()


def sender_hash(value, key):
    return hashlib.sha256((key + value).encode('utf-8')).hexdigest()[:16]


def fetch(session, url, params):
    pause()
    response = session.get(url, params=params, timeout=30)
    if response.status_code == 429:
        raise Stop(f'HTTP 429 at {response.url}')
    response.raise_for_status()
    return response.text


def parse_feed(html):
    posts = []
    for message in BeautifulSoup(html, 'html.parser').select('.tgme_widget_message[data-post]'):
        channel, number = message['data-post'].split('/')
        stamp = message.select_one('a.tgme_widget_message_date time[datetime]')
        if stamp is None:
            continue
        body = message.select_one('.tgme_widget_message_text')
        for br in body.find_all('br') if body else []:
            br.replace_with('\n')
        forwarded = message.select_one('.tgme_widget_message_forwarded_from')
        link = forwarded.select_one('a[href]') if forwarded else None
        source = link['href'] if link and re.match(r'https://t\.me/\w+/\d+', link['href']) else 'person_or_hidden'
        views = message.select_one('.tgme_widget_message_views')
        posts.append(dict(
            id=int(number), channel=channel, url=f'https://t.me/{channel}/{number}', published_at=stamp['datetime'],
            text=body.get_text('\n', strip=True) if body else '', forwarded_from=source if forwarded else None,
            media=[kind for kind, selector in MEDIA.items() if message.select_one(selector)],
            views=views.get_text(strip=True) if views else None))
    return posts


def search(session, channel, term, since):
    before = None
    while True:
        posts = parse_feed(fetch(session, f'https://t.me/s/{channel}', {'q': term, **({'before': before} if before else {})}))
        if not posts:
            return
        yield from (p for p in posts if p['published_at'][:10] >= since)
        oldest = min(posts, key=lambda p: p['id'])
        if oldest['published_at'][:10] < since or oldest['id'] <= 1 or before == oldest['id']:
            return
        before = oldest['id']


def load_comments(driver, channel, post_id, max_rounds=200):
    """Open the discussion widget and press "more" until all comments are shown.

    Returns (soup, status): status is complete (no "more" button left), partial ("more" stopped loading or
    max_rounds reached) or no_discussion (soup is None)."""
    driver.get(f'https://t.me/{channel}/{post_id}?embed=1&discussion=1')
    pause(3, 6)
    if 'Discussion is not available' in driver.page_source:
        return None, 'no_discussion'
    seen, status = -1, 'partial'
    for _ in range(max_rounds):
        count = len(driver.find_elements('css selector', '.tgme_widget_message[data-post-id]'))
        more = driver.find_elements('css selector', '.js-messages_more:not(.hide)')
        if not more:
            status = 'complete'
            break
        if count == seen:
            break
        seen = count
        driver.execute_script('arguments[0].scrollIntoView(); arguments[0].click();', more[0])
        pause(2, 4.5)
    return BeautifulSoup(driver.page_source, 'html.parser'), status


def parse_comments(soup, post, channel_title, key):
    """Comments of the widget. The quoted parent message is not part of the text."""
    rows = []
    for message in soup.select('.tgme_widget_message[data-post-id]'):
        stamp = message.select_one('time[datetime]')
        reply = message.select_one('.js-reply_to[data-reply-to]')
        texts = [t for t in message.select('.tgme_widget_message_text')
                 if 'js-message_reply_text' not in (t.get('class') or [])]
        for br in texts[0].find_all('br') if texts else []:
            br.replace_with('\n')
        author = next((a for a in message.select('.tgme_widget_message_author_name')
                       if not a.find_parent(class_='js-reply_to')), None)
        href = (author.get('href') or '') if author else ''
        username = href.rstrip('/').rsplit('/', 1)[-1] if 't.me/' in href else None
        display = author.get_text(' ', strip=True) if author else ''
        is_channel = (username or '').lower() == post['channel'].lower() or bool(channel_title and display == channel_title)
        rows.append(dict(
            post_id=post['id'], channel=post['channel'], id=int(message['data-post-id']),
            reply_to=int(reply['data-reply-to']) if reply else None,
            url=f"{post['url']}?comment={message['data-post-id']}",
            published_at=stamp['datetime'] if stamp else None,
            text=texts[0].get_text('\n', strip=True) if texts else '',
            sender_kind='channel' if is_channel else 'person',
            sender_hash=None if is_channel else sender_hash(username or f'name:{display}', key),
            _collected_at=now()))
    return rows


def write_jsonl(path, items):
    part = path.with_name(path.name + '.part')
    with part.open('w', encoding='utf-8') as stream:
        for item in items:
            stream.write(json.dumps(item, ensure_ascii=False) + '\n')
    part.rename(path)


def log_run(out, record):
    path = out / '_run.json'
    runs = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    path.write_text(json.dumps(runs + [record], ensure_ascii=False, indent=1), encoding='utf-8')


def collect_channel(session, driver_factory, channel, args, key, out):
    suffix = f'_pilot{args.max_comment_posts}' if args.max_comment_posts else ''
    posts_path, comments_path = out / f'posts_{channel}{suffix}.jsonl', out / f'comments_{channel}{suffix}.jsonl'
    if posts_path.exists():
        return {'status': 'skipped_exists'}
    found = {}
    for term in args.term or DEFAULT_TERMS:
        for post in search(session, channel, term, args.since):
            found.setdefault(post['id'], {**post, 'matched_terms': [], '_collected_at': now()})['matched_terms'].append(term)
    posts = sorted(found.values(), key=lambda p: p['id'])
    comments = []
    if not args.no_comments and posts:
        title = BeautifulSoup(fetch(session, f'https://t.me/s/{channel}', {}), 'html.parser').select_one('meta[property="og:title"]')
        driver = driver_factory()
        for post in posts[-args.max_comment_posts:] if args.max_comment_posts else posts:
            soup, post['comments_status'] = load_comments(driver, channel, post['id'])
            rows = parse_comments(soup, post, title['content'] if title else None, key) if soup else []
            post['comments_loaded'] = len(rows)
            comments += rows
    write_jsonl(posts_path, posts)
    if not args.no_comments:
        write_jsonl(comments_path, comments)
    statuses = Counter(p.get('comments_status', 'not_opened') for p in posts)
    return {'status': 'limited' if args.max_comment_posts else 'complete_for_run', 'posts': len(posts),
            'comments': len(comments), **{f'posts_{k}': v for k, v in sorted(statuses.items())}}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--channel', action='append', help='channel handle; repeatable; default: all channels from T01')
    parser.add_argument('--term', action='append', help=f'search term; repeatable; default: {DEFAULT_TERMS}')
    parser.add_argument('--since', default='2025-09-01', help='keep posts on or after this date, YYYY-MM-DD (default: 2025-09-01)')
    parser.add_argument('--max-comment-posts', type=int, help='open comments only under the N latest posts; for pilots')
    parser.add_argument('--no-comments', action='store_true', help='posts only, no browser')
    args = parser.parse_args()

    channels = args.channel or [re.sub(r'https://t\.me/', '', row['url']).strip('/')
                                for row in csv.DictReader(T01_CHANNELS.open(encoding='utf-8'))]
    out = ROOT / 'data/raw/telegram' / datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out.mkdir(parents=True, exist_ok=True)
    record = {'collector_version': VERSION, 'started_at': now(), 'errors': [], 'counts': {},
              'params': {**vars(args), 'channels': channels, 'term': args.term or DEFAULT_TERMS}}
    session = requests.Session()
    session.headers.update(HEADERS)
    drivers = []

    def driver_factory():
        if not drivers:
            from selenium import webdriver
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1200,1000')
            drivers.append(webdriver.Chrome(options=options))
            drivers[0].set_page_load_timeout(45)
        return drivers[0]

    try:
        for channel in channels:
            try:
                record['counts'][channel] = result = collect_channel(session, driver_factory, channel, args, salt(), out)
                print(channel, *result.values(), sep='\t', flush=True)
            except Stop:
                raise
            except Exception as error:  # one channel does not stop the others
                record['errors'].append(f'{channel}: {type(error).__name__}: {error}')
                print(channel, 'error', error, sep='\t', flush=True)
    except Stop as error:
        record['errors'].append(f'stopped: {error}')
        print(f'stopped: {error}. Wait, then rerun: finished channels are skipped.', file=sys.stderr)
    finally:
        for driver in drivers:
            driver.quit()
        record['finished_at'] = now()
        log_run(out, record)
    return 1 if record['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
