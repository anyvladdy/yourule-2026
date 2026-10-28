"""Collect Dzen articles and videos about Электрозавод and their comments, without login.

Brave runs headless in incognito with a throwaway profile that is deleted at exit (no cookies kept).
Reader pace: random 2-5 s before every page and 1.5-3.5 s between scroll or click steps.
A captcha, a login wall or "too many requests" stops the run; it is never worked around (card T16, A1).

Search results are filtered to items whose title or description mentions Электрозавод and not only
«Электрозаводская» (the metro station). Items published before --since are counted and dropped.
Comment authors are stored only as a salted hash (salt in .secrets/hash_salt, never printed).
@mentions in any text are replaced with [user].

Pilot: --pilot limits the run to 10 items. Files are appended, so a second run continues the same day's
folder: data/raw/dzen/<YYYY-MM-DD>/items.jsonl, comments.jsonl, _run.json (one record per run).
Summary counts without texts: out/run_summary.csv.

Example:
  .venv/bin/python workflow/stage1/T16_dzen/collect_dzen.py --pilot
"""
import argparse
import csv
import hashlib
import json
import random
import re
import secrets
import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from bs4 import BeautifulSoup

VERSION = 'dzen_web/0.1'
ROOT = Path(__file__).resolve().parents[3]
CARD = ROOT / 'workflow/stage1/T16_dzen'
BRAVE = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
DEFAULT_QUERY = 'Электрозавод'
WALL_MARKERS = ('Подтвердите, что вы не робот', 'SmartCaptcha', 'Слишком много запросов', 'Too many requests',
                'Доступ ограничен')
LOGIN_MARKERS = ('Войдите в аккаунт, чтобы продолжить',)
MONTHS = {'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'мая': 5, 'май': 5, 'июн': 6, 'июл': 7, 'авг': 8,
          'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12}
MONTH_WORD = r'(?:янв\w*|фев\w*|мар\w*|апр\w*|ма[йя]|июн\w*|июл\w*|авг\w*|сен\w*|окт\w*|ноя\w*|дек\w*)'
LABEL_RE = re.compile(r'(сегодня|вчера|\d+\s*(?:минут|час|дн|день|дня|дней|недел|месяц|год|лет)\w*\s+назад|'
                      r'\d{1,2}\s+' + MONTH_WORD + r'(?:\s+\d{4})?)', re.IGNORECASE)
MEDIA_TYPES = {'article': 'text', 'video': 'video'}
MASK = re.compile(r'@[A-Za-z0-9_]{2,}')


class Stop(Exception):
    """Dzen showed a wall: stop the run and report it."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def today_msk():
    return datetime.now(timezone.utc).astimezone().date()


def pause(low=2.0, high=5.0):
    time.sleep(random.uniform(low, high))


def salt():
    path = ROOT / '.secrets' / 'hash_salt'
    if not path.exists():
        path.parent.mkdir(exist_ok=True)
        path.write_text(secrets.token_hex(32), encoding='utf-8')
    return path.read_text(encoding='utf-8').strip()


def author_hash(value, key):
    return hashlib.sha256((key + value).encode('utf-8')).hexdigest()[:16]


def mask(text):
    return MASK.sub('[user]', text or '')


def clean(text):
    return re.sub(r'[ \t\u00a0]+', ' ', (text or '')).strip()


def hash_key(text):
    return re.sub(r'\W+', '', (text or '').lower())[:120]


def month_number(word):
    word = word.lower().replace('ё', 'е')
    if word.startswith('мар'):
        return 3
    return MONTHS.get(word[:3])


def parse_date_text(raw, base):
    """Date from a Dzen label: '21 июн', '22 июля 2022 года', 'вчера', '3 недели назад'.

    Returns (iso_date or None, note or None). A label without a year gets the collection year; if that
    lands in the future, the previous year is used."""
    text = clean(raw).lower().replace('ё', 'е')
    if not text:
        return None, None
    if 'сегодня' in text:
        return base.isoformat(), f"relative date '{raw}' resolved with collection date"
    if 'вчера' in text:
        return (base - timedelta(days=1)).isoformat(), f"relative date '{raw}' resolved with collection date"
    match = re.search(r'(\d+)\s*(минут|час|дн|недел|месяц|год|лет)\w*\s+назад', text)
    if match:
        number, unit = int(match.group(1)), match.group(2)
        steps = {'минут': timedelta(minutes=number), 'час': timedelta(hours=number), 'дн': timedelta(days=number),
                 'недел': timedelta(weeks=number), 'месяц': timedelta(days=30 * number),
                 'год': timedelta(days=365 * number), 'лет': timedelta(days=365 * number)}[unit]
        return (base - steps).isoformat(), f"relative date '{raw}' resolved with collection date (approximate)"
    match = re.search(r'(\d{1,2})\s+(' + MONTH_WORD + r')\s*(\d{4})?', text)
    if match:
        day, month = int(match.group(1)), month_number(match.group(2))
        if month is None:
            return None, f"unparsable date '{raw}'"
        year = int(match.group(3)) if match.group(3) else base.year
        try:
            value = date(year, month, day)
        except ValueError:
            return None, f"unparsable date '{raw}'"
        if not match.group(3) and value > base:
            value = date(year - 1, month, day)
            return value.isoformat(), f"date '{raw}' has no year; year {year - 1} inferred from collection date"
        return value.isoformat(), (None if match.group(3) else
                                   f"date '{raw}' has no year; year {year} inferred from collection date")
    return None, f"unparsable date '{raw}'"


def relevant_text(*parts):
    """Электрозавод in any case form, but not only through «Электрозаводская» (metro, street, railway)."""
    text = ' '.join(part for part in parts if part)
    without_metro = re.sub(r'электрозаводск\w*', ' ', text, flags=re.IGNORECASE)
    return bool(re.search(r'электрозавод', without_metro, flags=re.IGNORECASE))


def item_kind(url):
    if '/video/watch/' in url:
        return 'video'
    if re.search(r'/a/[\w-]+', url):
        return 'article'
    return 'other'


def open_driver(tmp):
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    options.binary_location = BRAVE
    for flag in ('--headless=new', '--incognito', f'--user-data-dir={tmp}', '--no-first-run', '--disable-gpu',
                 '--no-sandbox', '--window-size=1400,1800', '--lang=ru-RU'):
        options.add_argument(flag)
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver


def incognito_confirmed(driver):
    """Read the browser command line: the run is logged as incognito only when the flag is there."""
    try:
        driver.get('brave://version')
        time.sleep(1)
        text = driver.execute_script('return document.body.innerText')
        line = next((row for row in text.splitlines() if row.startswith('Command Line')), '')
        return '--incognito' in line
    except Exception:
        return False


def page_text(driver):
    return driver.execute_script('return document.body ? document.body.innerText : ""')


def check_walls(driver, stage):
    text = page_text(driver)
    for marker in WALL_MARKERS + LOGIN_MARKERS:
        if marker.lower() in text.lower():
            raise Stop(f'{stage}: wall "{marker}" at {driver.current_url}')
    if re.search(r'(showcaptcha|captcha|passport\.yandex)', driver.current_url):
        raise Stop(f'{stage}: captcha/auth redirect {driver.current_url}')


def scroll(driver, steps, low=1.5, high=3.5):
    for _ in range(steps):
        driver.execute_script(f'window.scrollBy(0, Math.round(window.innerHeight * {0.7 + random.random() * 0.3:.2f}))')
        time.sleep(random.uniform(low, high))


def search_rows(driver, query, max_scrolls, max_rows):
    """Search page: scroll until no new rows, return rows in page order (deduplicated by URL)."""
    driver.get(f'https://dzen.ru/search?query={query}')
    pause(3, 6)
    check_walls(driver, 'search')
    seen, rows, empty, last_count = set(), [], 0, -1
    for step in range(max_scrolls):
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for row in soup.select('[data-testid="feed-row"]'):
            link = row.select_one('a[href*="/a/"], a[href*="/video/watch/"]')
            if not link:
                continue
            url = link['href'].split('?')[0]
            if url in seen:
                continue
            seen.add(url)
            title = row.select_one('[data-testid="card-part-title"]')
            desc = row.select_one('[data-testid="card-part-description"]')
            author = None
            for anchor in row.select('a[href]'):
                name = clean(anchor.get_text(' ', strip=True))
                if name and re.match(r'https://dzen\.ru/(?!a/|video/|news/)[\w.-]+', anchor['href']):
                    author = {'name': name, 'url': anchor['href'].split('?')[0]}
                    break
            row_text = clean(row.get_text(' | ', strip=True))
            match = LABEL_RE.search(row_text)
            date_label = match.group(0) if match else None
            rows.append({'url': url, 'title': clean(title.get_text(' ', strip=True)) if title else None,
                         'description': clean(desc.get_text(' ', strip=True)) if desc else None,
                         'author': author, 'date_label': date_label, 'row_text': row_text[:400],
                         'query': query, 'position': len(rows)})
        empty = empty + 1 if len(seen) == last_count else 0
        last_count = len(seen)
        print(f'  search step {step}: {len(seen)} rows', flush=True)
        if len(seen) >= max_rows or empty >= 3:
            break
        scroll(driver, 1)
    return rows


def publisher_from_html(html, soup):
    """Channel name and link: a named channel keeps its name; a private person's page holds /id/<hash>."""
    name_match = re.search(r'"authorName":"([^"]{1,120})"', html)
    url_match = re.search(r'"publisherUrl":"(https://dzen\.ru/[^"]{1,160})"', html)
    name = name_match.group(1) if name_match else None
    publisher_url = url_match.group(1) if url_match else None
    if not name:
        block = soup.select_one('[data-testid="publisher-block-inline"]')
        anchor = block.select_one('a[href]') if block else None
        if anchor:
            name = clean(anchor.get_text(' ', strip=True))
            href = anchor.get('href') or ''
            publisher_url = 'https://dzen.ru' + href if href.startswith('/') else href
    return name, publisher_url


def item_date(html, soup):
    meta = soup.select_one('meta[itemprop="datePublished"]')
    if meta and re.fullmatch(r'\d{4}-\d{2}-\d{2}', meta.get('content', '')):
        return meta['content'], 'meta datePublished'
    match = re.search(r'"publishDate":"(\d{4}-\d{2}-\d{2})', html)
    if match:
        return match.group(1), 'publisher JSON publishDate'
    return None, None


def comment_counter(sec):
    node = sec.select_one('[data-testid="comments-header-counter-text"]') if sec else None
    text = clean(node.get_text(' ', strip=True)) if node else ''
    match = re.search(r'\d+', text)
    return int(match.group(0)) if match else None


COMMENTS_SELECTOR = ('[data-testid="article-comments"], [data-testid="video-viewer-comments"], '
                     '[data-testid="video-modal-comments"]')


def wait_for_comments(driver, timeout=25):
    """The comment list loads lazily: wait for its first item or for the empty-state text."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = driver.execute_script('''
            const section = document.querySelector('[data-testid="article-comments"], [data-testid="video-viewer-comments"], [data-testid="video-modal-comments"]');
            if (!section) return 'no_section';
            if (section.querySelector('[data-testid="root-comment"]')) return 'loaded';
            if (/станет первым/.test(section.innerText)) return 'empty';
            return 'pending';
        ''')
        if state == 'empty':
            time.sleep(5)  # a list that is still loading shows the empty state for a moment
            again = driver.execute_script('''
                const section = document.querySelector('[data-testid="article-comments"], [data-testid="video-viewer-comments"], [data-testid="video-modal-comments"]');
                if (!section) return 'no_section';
                if (section.querySelector('[data-testid="root-comment"]')) return 'loaded';
                return /станет первым/.test(section.innerText) ? 'empty' : 'pending';
            ''')
            if again == 'empty':
                return 'empty'
            state = again
        if state in ('loaded', 'no_section'):
            return state
        scroll(driver, 1, 1.0, 2.0)
    return 'timeout'


def expand_comments(driver, max_rounds):
    """Reveal every reply and every 'show more' block; a captcha stops the run instead of retrying."""
    driver.execute_script('document.querySelector(\'[data-testid="article-comments"], [data-testid="video-viewer-comments"], [data-testid="video-modal-comments"]\')?.scrollIntoView({block:"start"})')
    pause(2.0, 3.5)
    pattern = re.compile(r'^(?:ещё\s+\d+(?:\s+ответ\w*|\s+коммент\w*)?|\d+\s+ответ\w*|показать\s+(?:ещё|все))$',
                         re.IGNORECASE)
    quiet = 0
    for _ in range(max_rounds):
        clicked = 0
        for ellipsis in driver.find_elements('css selector', '[data-testid="rich-text-expand-ellipsis"]'):
            try:
                if ellipsis.is_displayed():
                    driver.execute_script('arguments[0].click();', ellipsis)
                    clicked += 1
                    time.sleep(random.uniform(0.6, 1.4))
            except Exception:
                continue
        for button in driver.find_elements('css selector', 'button'):
            try:
                label = clean(button.text).lower()
            except Exception:
                continue
            if not label or not pattern.match(label) or not button.is_displayed():
                continue
            driver.execute_script('arguments[0].scrollIntoView({block:"center"}); arguments[0].click();', button)
            clicked += 1
            time.sleep(random.uniform(1.2, 2.5))
        quiet = quiet + 1 if clicked == 0 else 0
        if quiet >= 2:
            break
    check_walls(driver, 'comments')
    scroll(driver, 2, 1.0, 2.0)


def parse_comment(node, key, base, item_id, index, parent_index, kind):
    link = node.select_one('[data-testid="comment-author-link"]')
    href = (link.get('href') or '') if link else ''
    name = clean(link.get_text(' ', strip=True)) if link else ''
    date_node = node.select_one('[class*="common-date__text"]')
    label = clean(date_node.get_text(' ', strip=True)) if date_node else ''
    published, note = parse_date_text(label, base) if label else (None, 'no date shown')
    body = node.select_one('[class*="comment-text__block"]')
    if body is not None:
        for quoted in body.select('[data-testid="comment-author-name"]'):
            quoted.decompose()  # the addressee's name, not the comment text (R5)
    text = body.get_text('\n', strip=True) if body else ''
    text = re.sub(r'^[\s,;:—-]+', '', text)
    like = node.select_one('[data-testid="reaction-like-count"]')
    is_channel = bool(href) and not href.startswith(('/id/', '/user/'))
    return {
        'id': f'{item_id}-{kind}{index}', 'source': 'dzen', 'parent_id': parent_index,
        'thread_id': item_id, 'url': None, 'url_note': 'Dzen shows no per-comment anchor',
        'author_id_hash': author_hash(href or f'name:{name}', key) if (href or name) else None,
        'author_type': 'channel' if is_channel else ('person' if href else 'unknown'),
        'author_display': None, 'published_at': published, 'date_label': label or None, 'collected_at': now(),
        'text': mask(text), 'lang': 'ru', 'media_type': None, 'likes': clean(like.get_text()) if like else None,
        'depth': 1 if kind == 'child' else 0, 'note': note,
    }


def parse_comments(soup, key, base, item_id):
    sec = soup.select_one(COMMENTS_SELECTOR)
    if not sec:
        return [], {'status': 'no_comments_section', 'loaded': 0, 'hidden': 0, 'counter': None}
    rows, hidden = [], 0
    for root in sec.select('[data-testid="root-comment"]'):
        rows.append(parse_comment(root, key, base, item_id, len(rows), None, 'root'))
        parent = len(rows) - 1
        for child in root.select('[data-testid="child-comment"]'):
            if 'Алгоритмы скрыли' in child.get_text(' ', strip=True):
                hidden += 1
                continue
            rows.append(parse_comment(child, key, base, item_id, len(rows), parent, 'child'))
    rows = [row for row in rows if row['text']]
    counter = comment_counter(sec)
    if counter is None and not rows:
        counter, status = 0, 'empty'
    else:
        status = 'complete_for_run'
    return rows, {'status': status, 'loaded': len(rows), 'hidden': hidden, 'counter': counter}


def collect_item(driver, row, key, args, base):
    driver.get(row['url'])
    pause(args.page_pause_low, args.page_pause_high)
    check_walls(driver, 'item')
    scroll(driver, 3 if item_kind(row['url']) == 'video' else 5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    title_node = soup.select_one('h1') or soup.select_one('[data-testid="article-title"]')
    og_title = soup.select_one('meta[property="og:title"]')
    title = (clean(title_node.get_text(' ', strip=True)) if title_node
             else (clean(og_title.get('content')) if og_title and og_title.get('content') else (row['title'] or '')))
    published, date_source = item_date(html, soup)
    name, publisher_url = publisher_from_html(html, soup)
    body = soup.select_one('[data-testid="article-body"]')
    text = body.get_text('\n', strip=True) if body else ''
    author_is_person = bool(publisher_url and '/id/' in publisher_url)
    kind = item_kind(row['url'])
    item = {
        'id': row['url'].rstrip('/').rsplit('/', 1)[-1], 'source': 'dzen', 'url': row['url'],
        'item_kind': kind, 'parent_id': None, 'thread_id': None,
        'author_id_hash': author_hash(publisher_url, key) if author_is_person else None,
        'author_type': 'person' if author_is_person else ('media' if name else 'unknown'),
        'author_display': None if author_is_person else name,
        'publisher_url_hash': author_hash(publisher_url, key) if publisher_url else None,
        'published_at': published, 'date_source': date_source,
        'collected_at': now(), 'title': mask(title), 'text': mask(text), 'lang': 'ru',
        'media_type': MEDIA_TYPES.get(kind), 'views': None, 'likes': None, 'reposts': None,
        'comments_count': None, 'query': row['query'], 'position': row['position'],
        'matched_keywords': ['Электрозавод'], 'search_date_label': row['date_label'],
        'duplicate_of': None, 'note': None, 'collector_version': VERSION,
    }
    comments, status = [], {'status': 'skipped', 'loaded': 0, 'hidden': 0, 'counter': None}
    if not args.no_comments:
        state = wait_for_comments(driver, args.comments_wait)
        for attempt in range(3):
            expand_comments(driver, args.max_comment_rounds)
            comments, status = parse_comments(BeautifulSoup(driver.page_source, 'html.parser'), key, base, item['id'])
            if status['counter'] is None or status['loaded'] >= status['counter']:
                break
            print(f"  comments {status['loaded']}/{status['counter']}, attempt {attempt + 1}", flush=True)
            pause()
        if status['status'] == 'no_comments_section':
            status['status'] = 'not_rendered' if state != 'no_section' else 'no_section'
    item['comments_count'] = status['counter']
    item['comments_loaded'] = status['loaded']
    item['comments_hidden'] = status['hidden']
    item['comments_status'] = status['status']
    notes = []
    if item['comments_count'] is not None and status['loaded'] < item['comments_count']:
        notes.append(f"loaded {status['loaded']} of {item['comments_count']} comments")
        if status['hidden']:
            notes.append(f"{status['hidden']} comments hidden by the platform filter")
    if published is None and row['date_label']:
        fallback, fallback_note = parse_date_text(row['date_label'], base)
        item['published_at'] = fallback
        page_note = 'the page shows no publication date' if kind == 'video' else 'date taken from the search card'
        notes += [part for part in (page_note, fallback_note) if part]
    item['note'] = '; '.join(notes) or None
    return item, comments


def load_seen(items_path):
    if not items_path.exists():
        return set()
    ids = set()
    for line in items_path.read_text(encoding='utf-8').splitlines():
        try:
            ids.add(json.loads(line)['id'])
        except Exception:
            continue
    return ids


def load_titles(items_path):
    titles = {}
    if not items_path.exists():
        return titles
    for line in items_path.read_text(encoding='utf-8').splitlines():
        try:
            old = json.loads(line)
        except Exception:
            continue
        if old.get('title'):
            titles.setdefault(hash_key(old['title']), old['id'])
    return titles


def write_line(path, record):
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')


def log_run(out, record):
    path = out / '_run.json'
    runs = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    path.write_text(json.dumps(runs + [record], ensure_ascii=False, indent=1), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--query', action='append', help=f'search query; repeatable; default: {DEFAULT_QUERY}')
    parser.add_argument('--since', default='2025-09-01', help='keep items on or after this date (default: 2025-09-01)')
    parser.add_argument('--pilot', action='store_true', help='stop after 10 items (pilot per the card)')
    parser.add_argument('--max-items', type=int, default=100, help='ceiling for items opened in this run (default: 100)')
    parser.add_argument('--max-scrolls', type=int, default=40, help='search page scroll limit (default: 40)')
    parser.add_argument('--max-search-rows', type=int, default=100, help='search rows to keep (default: 100)')
    parser.add_argument('--max-comment-rounds', type=int, default=60, help='comment expansion rounds (default: 60)')
    parser.add_argument('--comments-wait', type=int, default=25, help='seconds to wait for the lazy comment list (default: 25)')
    parser.add_argument('--page-pause-low', type=float, default=2.0)
    parser.add_argument('--page-pause-high', type=float, default=5.0)
    parser.add_argument('--no-comments', action='store_true', help='items only, no comments')
    args = parser.parse_args()

    queries = args.query or [DEFAULT_QUERY]
    limit = 10 if args.pilot else args.max_items
    out = ROOT / 'data/raw/dzen' / today_msk().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    summary_path = CARD / 'out' / 'run_summary.csv'
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    base = today_msk()
    key = salt()
    run_name = 'pilot' if args.pilot else f'full_max{limit}'
    record = {'collector_version': VERSION, 'run': run_name, 'started_at': now(), 'query': queries,
              'since': args.since, 'limit': limit, 'errors': [], 'counts': {}, 'stopped_reason': None,
              'incognito_confirmed': None, 'notes': []}
    counts = {'items_found': 0, 'items_relevant': 0, 'items_since_2025_09': 0, 'items_older': 0,
              'items_duplicate': 0, 'comments': 0, 'rows_scanned': 0}
    tmp = tempfile.TemporaryDirectory(prefix='dzen_')
    driver = open_driver(tmp.name)
    try:
        record['incognito_confirmed'] = incognito_confirmed(driver)
        if not record['incognito_confirmed']:
            raise Stop('browser did not start in incognito mode; refusing to collect')
        rows = []
        for query in queries:
            rows += search_rows(driver, query, args.max_scrolls, args.max_search_rows)
            pause()
        counts['rows_scanned'] = len(rows)
        filtered, seen_urls = [], set()
        for row in rows:
            if row['url'] in seen_urls:
                continue
            seen_urls.add(row['url'])
            if relevant_text(row['title'], row['description']):
                filtered.append(row)
        counts['items_found'] = len(filtered)
        candidates = []
        for row in filtered:
            estimate_iso, _ = parse_date_text(row['date_label'], base) if row['date_label'] else (None, None)
            estimate = date.fromisoformat(estimate_iso) if estimate_iso else None
            if estimate and estimate < date.fromisoformat(args.since):
                counts['items_older'] += 1  # the search card says it is older: the page is not opened
                continue
            candidates.append((estimate, row))
        candidates.sort(key=lambda pair: pair[0] or date.min, reverse=True)
        filtered = [row for _, row in candidates]
        print(f'{len(rows)} search rows, {len(filtered)} recent items to open', flush=True)
        items_path, comments_path = out / 'items.jsonl', out / 'comments.jsonl'
        seen_ids = load_seen(items_path)
        titles = load_titles(items_path)
        opened = 0
        for row in filtered:
            if opened >= limit:
                break
            item_id = row['url'].rstrip('/').rsplit('/', 1)[-1]
            if item_id in seen_ids:
                continue
            try:
                item, comments = collect_item(driver, row, key, args, base)
            except Stop:
                raise
            except Exception as error:  # one page does not stop the others
                record['errors'].append(f"{row['url']}: {type(error).__name__}: {error}")
                print('  error', row['url'], type(error).__name__, error, flush=True)
                continue
            opened += 1
            if item['published_at'] and item['published_at'] < args.since:
                counts['items_older'] += 1
                print('  older', item['published_at'], item['title'][:60], flush=True)
                continue
            counts['items_relevant'] += 1
            duplicate = titles.get(hash_key(item['title']))
            if duplicate:
                item['duplicate_of'] = duplicate
                counts['items_duplicate'] += 1
            else:
                titles[hash_key(item['title'])] = item['id']
            write_line(items_path, item)
            seen_ids.add(item['id'])
            for comment in comments:
                write_line(comments_path, comment)
            counts['items_since_2025_09'] += 1
            counts['comments'] += len(comments)
            print(f"  [{opened}/{limit}] {item['published_at']} c={len(comments)} {item['title'][:70]}", flush=True)
    except Stop as error:
        record['stopped_reason'] = str(error)
        record['errors'].append(f'stopped: {error}')
        print(f'stopped: {error}', file=sys.stderr, flush=True)
    finally:
        try:
            driver.quit()
        finally:
            tmp.cleanup()
        record['finished_at'] = now()
        record['counts'] = counts
        if record['stopped_reason'] is None:
            record['stopped_reason'] = 'pilot limit reached' if args.pilot else 'item ceiling reached or list exhausted'
        record['notes'] = [
            'comment ids are positional inside the page: Dzen shows no per-comment anchor or id',
            'comment dates are short labels like "21 июн": the year is inferred from the collection date and noted per row',
            'views are not shown on Dzen article pages: views = null',
        ]
        log_run(out, record)
        new_row = {'run': run_name, 'items_found': counts['items_found'],
                   'items_relevant': counts['items_relevant'],
                   'items_since_2025_09': counts['items_since_2025_09'],
                   'comments': counts['comments'], 'stopped_reason': record['stopped_reason']}
        existing = summary_path.read_text(encoding='utf-8') if summary_path.exists() else ''
        with summary_path.open('a', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(new_row))
            if not existing.strip():
                writer.writeheader()
            writer.writerow(new_row)
        print(json.dumps(counts, ensure_ascii=False), flush=True)
        print('stopped_reason:', record['stopped_reason'], flush=True)
    return 1 if record['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
