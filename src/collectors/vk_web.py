"""Collect public VK posts and comments about Электрозавод in a browser where the user logs in by hand (D-21).

Run from the repository root.

  browser   open Brave in incognito with a fresh temporary profile at the VK login page; log in there yourself
  status    check that the browser is reachable and logged in (prints cookie names only, never values)
  snapshot  pilot: open the given URLs, scroll at reader pace, save the page HTML to check selectors before collecting
  collect   posts from the global post search and from the post search inside each community (the search button on
            the community page), then comments under posts that mention the site
  close     close that Brave window and delete its temporary profile

Authors who are people are stored only as a salted hash (salt in .secrets/hash_salt); communities keep their name.
Dates are shown by VK in Moscow time ("13 окт", "8 июл 2025", "вчера в 14:05"); the raw text is kept next to the parsed date.

Every command after `browser` attaches to the same window through a local debugging port, so you log in once.
The port listens on 127.0.0.1 only; run `close` when the collection is over.
Reader pace: random pauses and slow scrolling. A captcha, a "too many requests" page or a logout stops the run and
asks you to act; it is never worked around (AGENTS §3). Raw pages go to data/raw/vk/<YYYY-MM-DD>/ (not in git).
"""
import argparse
import hashlib
import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.secrets' / 'vk_browser.json'
BROWSERS = {'brave': '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
            'chrome': '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}
PORT = 9222
SESSION_COOKIES = ('remixsid', 'remixnsid')
WALLS = ('Подтвердите, что вы не робот', 'Слишком много запросов', 'Too many requests')
VK_HOST = re.compile(r'^https://([a-z]+\.)?vk\.(com|ru)/')  # vk.com redirects to vk.ru (seen 2026-10-28)
LOGIN_PAGES = re.compile(r'^https://(id\.vk\.(com|ru)|(m\.)?vk\.(com|ru)/login)')
DEFAULT_SNAPSHOTS = ['https://vk.ru/search/statuses?q=Электрозавод',
                     'https://vk.ru/search?c%5Bq%5D=Электрозавод&c%5Bsection%5D=statuses',
                     'https://vk.ru/sokgor']
DEFAULT_COMMUNITIES = ['sokgor', 'club230930257']  # district groups found in T13
VERSION = 'vk_web/0.1'
SITE = re.compile(r'электрозавод(?!ск)', re.IGNORECASE)
MSK = timezone(timedelta(hours=3))
MONTHS = {'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'мая': 5, 'май': 5, 'июн': 6, 'июл': 7, 'авг': 8, 'сен': 9,
          'окт': 10, 'ноя': 11, 'дек': 12}
MORE = re.compile(r'показать (следующие|ещё|еще|все|предыдущие)|ещё \d+ (ответ|коммент)|показать \d+ (ответ|коммент)',
                  re.IGNORECASE)


class Stop(Exception):
    """VK showed a captcha, a limit or a logout: the user has to act."""


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def salt():
    path = ROOT / '.secrets' / 'hash_salt'
    if not path.exists():
        sys.exit('No .secrets/hash_salt: run the Telegram collector once or create it as in telegram_web.py')
    return path.read_text(encoding='utf-8').strip()


def person_hash(owner_id, key):
    return hashlib.sha256((key + 'vk:' + owner_id).encode('utf-8')).hexdigest()[:16]


def parse_date(text, today=None):
    """VK display date in Moscow time → ISO datetime (UTC) when the time is shown, ISO date otherwise; None if unknown."""
    if not text:
        return None
    t = text.strip().lower()
    today = today or datetime.now(MSK).date()
    if 'только что' in t or 'назад' in t:
        return today.isoformat()
    if t.startswith('сегодня'):
        day = today
    elif t.startswith('вчера'):
        day = today - timedelta(days=1)
    else:
        m = re.match(r'(\d{1,2})\s+([а-я]{3})[а-я]*\.?(?:\s+(\d{4}))?', t)
        if not m or m[2] not in MONTHS:
            return None
        day = date(int(m[3]) if m[3] else today.year, MONTHS[m[2]], int(m[1]))
        if not m[3] and day > today:
            day = day.replace(year=day.year - 1)
    clock = re.search(r'в\s+(\d{1,2}):(\d{2})', t)
    if clock:
        moment = datetime(day.year, day.month, day.day, int(clock[1]), int(clock[2]), tzinfo=MSK)
        return moment.astimezone(timezone.utc).isoformat()
    return day.isoformat()


def counter(element, testid):
    found = element.select_one(f'[data-testid="{testid}"]')
    value = found.get_text(' ', strip=True) if found else ''
    return value or None


def parse_posts(html, source, key):
    rows = []
    for post in BeautifulSoup(html, 'html.parser').select('div[data-post-id][data-post-nesting-lvl="0"]'):
        post_id = post['data-post-id']
        owner = post_id.split('_')[0]
        person = not owner.startswith('-')
        title = post.select_one('[data-testid="post-header-title"]')
        body = post.select_one('[data-testid="showmoretext-in"]') or post.select_one('[data-testid="post_text"]')
        for mention in body.select('[data-testid="post-text-mention"], [data-testid="mention"]') if body else []:
            mention.replace_with('[user]')
        text = body.get_text('\n', strip=True) if body else ''
        raw_date = counter(post, 'post_date_block_preview')
        rows.append(dict(
            id=post_id, source=source, url=f'https://vk.ru/wall{post_id}', owner_kind='person' if person else 'community',
            author_display=None if person or not title else title.get_text(' ', strip=True),
            author_hash=person_hash(owner, key) if person else None,
            published_raw=raw_date, published_at=parse_date(raw_date), text=text,
            likes=counter(post, 'post_footer_action_like'), comments=counter(post, 'post_footer_action_comment'),
            reposts=counter(post, 'post_footer_action_share'), mentions_site=bool(SITE.search(text)),
            _collected_at=now_utc()))
    return rows


def parse_comments(html, post, key):
    rows, thread = [], None
    selector = '[data-testid="wall_comments_comment_root"], [data-testid="wall_comments_comment_in_thread"]'
    for item in BeautifulSoup(html, 'html.parser').select(selector):
        author, _, comment_id = (item.get('id') or '_').partition('_')
        root = item['data-testid'] == 'wall_comments_comment_root'
        if root:
            thread = comment_id
        community = author.startswith('-')
        owner = item.select_one('[data-testid="comment-owner"]')
        body = item.select_one('[data-testid="comment-text"]')
        for mention in body.select('[data-testid="mention"]') if body else []:  # "Наталья, ..." in replies
            mention.replace_with('[user]')
        raw_date = counter(item, 'wall_comment_date')
        rows.append(dict(
            id=f"{post['id']}_c{comment_id}", post_id=post['id'], parent_id=post['id'] if root else f"{post['id']}_c{thread}",
            thread_id=f"{post['id']}_c{thread}", url=f"{post['url']}?reply={comment_id}",
            author_kind='community' if community else 'person',
            author_hash=None if community else person_hash(author, key),
            author_display=owner.get_text(' ', strip=True) if community and owner else None,
            is_post_owner=author == post['id'].split('_')[0],
            published_raw=raw_date, published_at=parse_date(raw_date),
            text=body.get_text('\n', strip=True) if body else '', likes=counter(item, 'comment-like'),
            _collected_at=now_utc()))
    return rows


def scroll_and_collect(driver, parse, max_items=None, rounds=3, max_steps=400):
    """VK keeps only the visible part of a long list in the page, so parse after every scroll step and merge by id.
    More results load only at the bottom of the page: stop when `rounds` steps in a row at the bottom add nothing,
    or at max_items."""
    found, still = {}, 0
    for _ in range(max_steps):
        if still >= rounds or (max_items and len(found) >= max_items):
            break
        before = len(found)
        for row in parse(driver.page_source):
            found.setdefault(row['id'], row)
        at_bottom = driver.execute_script('return window.innerHeight + window.scrollY >= document.body.scrollHeight - 50')
        still = still + 1 if len(found) == before and at_bottom else 0
        driver.execute_script('window.scrollBy(0, Math.round(window.innerHeight * (0.6 + Math.random() * 0.3)))')
        pause(1.5, 3.5)
        check(driver)
    return list(found.values())


def type_slowly(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.08, 0.25))


def load_all_comments(driver, parse, max_rounds=40):
    """Scroll and press "show more comments / replies" until nothing new appears; parse after every step."""
    found = {}
    for _ in range(max_rounds):
        for row in parse(driver.page_source):
            found.setdefault(row['id'], row)
        clicked = driver.execute_script("""
            const re = new RegExp(arguments[0], 'i');
            const el = Array.from(document.querySelectorAll('button, a, [role=button], span'))
              .find(e => e.offsetWidth > 0 && re.test((e.innerText || '').trim()) && (e.innerText || '').length < 60);
            if (el) { el.scrollIntoView({block: 'center'}); el.click(); return true; } return false;""", MORE.pattern)
        driver.execute_script('window.scrollBy(0, Math.round(window.innerHeight * (0.6 + Math.random() * 0.3)))')
        pause(1.5, 3.5)
        check(driver)
        if not clicked and driver.execute_script(
                'return window.innerHeight + window.scrollY >= document.body.scrollHeight - 50'):
            break
    for row in parse(driver.page_source):
        found.setdefault(row['id'], row)
    return list(found.values())


def pause(low=2.0, high=5.0):
    time.sleep(random.uniform(low, high))


def out_dir():
    path = ROOT / 'data/raw/vk' / datetime.now(timezone.utc).strftime('%Y-%m-%d')
    path.mkdir(parents=True, exist_ok=True)
    return path


def attach():
    if not STATE.exists():
        sys.exit('No browser started: run `vk_web.py browser` first')
    from selenium import webdriver
    options = webdriver.ChromeOptions()
    options.binary_location = json.loads(STATE.read_text())['binary']
    options.debugger_address = f'127.0.0.1:{PORT}'
    return webdriver.Chrome(options=options)


def check(driver):
    """Stop on a visible captcha or wall. The page source always contains "captcha" in config flags, so only
    visible elements and visible text count."""
    visible = driver.execute_script(
        "return Array.from(document.querySelectorAll('[class*=aptcha], [id*=aptcha], iframe[src*=captcha]'))"
        ".filter(e => e.offsetWidth > 0 && e.offsetHeight > 0).length")
    text = driver.execute_script('return document.body ? document.body.innerText : ""')
    hit = 'visible captcha' if visible else next((w for w in WALLS if w in text), None)
    if hit:
        raise Stop(f'"{hit}" on {driver.current_url}')
    if LOGIN_PAGES.match(driver.current_url):
        raise Stop(f'not logged in: {driver.current_url}')


def logged_in(driver):
    if not VK_HOST.match(driver.current_url) or LOGIN_PAGES.match(driver.current_url):
        return False, []  # never navigate away while the user is on a login page
    names = sorted(c['name'] for c in driver.get_cookies())
    return any(n in names for n in SESSION_COOKIES), names


def cmd_browser(args):
    if STATE.exists():
        sys.exit('A browser is already registered: run `vk_web.py close` first')
    profile = tempfile.mkdtemp(prefix='vk_browser_')
    process = subprocess.Popen(
        [BROWSERS[args.browser], '--incognito', f'--remote-debugging-port={PORT}', '--remote-debugging-address=127.0.0.1',
         f'--user-data-dir={profile}', '--no-first-run', '--no-default-browser-check', 'https://vk.com/login'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({'pid': process.pid, 'profile': profile, 'binary': BROWSERS[args.browser]}))
    print(f'{args.browser} is open in incognito. Log in to VK in that window, then run `vk_web.py status`.')


def cmd_status(args, driver):
    ok, names = logged_in(driver)
    print('logged in' if ok else 'NOT logged in', '| url:', driver.current_url, '| cookie names:', ', '.join(names))
    return 0 if ok else 1


def cmd_snapshot(args, driver):
    if not logged_in(driver)[0]:
        raise Stop('not logged in: log in in the browser window')
    folder = out_dir() / 'snapshots'
    folder.mkdir(exist_ok=True)
    for url in args.url or DEFAULT_SNAPSHOTS:
        pause()
        driver.get(url)
        pause(3, 6)
        check(driver)
        for _ in range(args.scrolls):
            driver.execute_script('window.scrollBy(0, Math.round(window.innerHeight * (0.6 + Math.random() * 0.3)))')
            pause(1.5, 3.5)
            check(driver)
        name = re.sub(r'[^A-Za-z0-9]+', '_', url.split('//', 1)[-1])[:80] + '.html'
        (folder / name).write_text(driver.page_source, encoding='utf-8')
        print(name, len(driver.page_source), driver.current_url, sep='\t')


def number(value):
    if not value:
        return None
    m = re.match(r'([\d.,]+)\s*([KkКк]?)', value.replace('\xa0', ''))
    if not m:
        return None
    base = float(m[1].replace(',', '.'))
    return int(base * 1000) if m[2] else int(base)


def write_jsonl(path, items):
    part = path.with_name(path.name + '.part')
    with part.open('w', encoding='utf-8') as stream:
        for item in items:
            stream.write(json.dumps(item, ensure_ascii=False) + '\n')
    part.rename(path)


def open_global_search(driver, term):
    driver.get('https://vk.ru/search/statuses?q=' + term)
    pause(3, 6)
    check(driver)


def open_community_search(driver, slug, term):
    from selenium.webdriver.common.keys import Keys
    driver.get(f'https://vk.ru/{slug}')
    pause(3, 6)
    check(driver)
    button = driver.find_element('css selector', '[data-testid="community-tabs-search-button"]')
    driver.execute_script('arguments[0].scrollIntoView({block: "center"});', button)
    pause(1, 2)
    button.click()
    pause(1.5, 3)
    field = driver.switch_to.active_element
    type_slowly(field, term)
    pause(0.5, 1.5)
    field.send_keys(Keys.ENTER)
    pause(3, 6)
    check(driver)


def collect_source(driver, source, opener, args, key, out):
    suffix = (f'_pilot{args.max_comment_posts}' if args.max_comment_posts else '') + (f'_{args.tag}' if args.tag else '')
    posts_path, comments_path = out / f'posts_{source}{suffix}.jsonl', out / f'comments_{source}{suffix}.jsonl'
    if posts_path.exists():
        return {'status': 'skipped_exists'}
    opener(driver)
    posts = scroll_and_collect(driver, lambda html: parse_posts(html, source, key), args.max_posts)
    targets = [p for p in posts if p['mentions_site'] and (p['published_at'] or '') >= args.since
               and (number(p['comments']) or 0) > 0]
    comments, statuses = [], {}
    for post in targets[:args.max_comment_posts] if args.max_comment_posts else targets:
        pause()
        driver.get(post['url'])
        pause(3, 6)
        check(driver)
        rows = load_all_comments(driver, lambda html, post=post: parse_comments(html, post, key))
        expected = number(post['comments'])
        post['comments_loaded'] = len(rows)
        post['comments_status'] = 'complete' if expected is None or len(rows) >= expected else 'partial'
        statuses[post['comments_status']] = statuses.get(post['comments_status'], 0) + 1
        comments += rows
    write_jsonl(posts_path, posts)
    write_jsonl(comments_path, comments)
    return {'status': 'limited' if args.max_comment_posts else 'complete_for_run', 'posts': len(posts),
            'posts_mentioning_site': sum(p['mentions_site'] for p in posts), 'comment_posts_opened': len(
                targets[:args.max_comment_posts] if args.max_comment_posts else targets),
            'comments': len(comments), **{f'posts_{k}': v for k, v in sorted(statuses.items())}}


def cmd_collect(args, driver):
    ok, _ = logged_in(driver)
    if not ok:
        raise Stop('not logged in: log in in the browser window')
    key, out = salt(), out_dir()
    record = {'collector_version': VERSION, 'started_at': now_utc(), 'params': vars(args), 'counts': {}, 'errors': []}
    from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
    sources = ([] if args.no_global else [('search', lambda drv: open_global_search(drv, args.term))]) + [
        (slug, lambda drv, slug=slug: open_community_search(drv, slug, args.term)) for slug in args.community or DEFAULT_COMMUNITIES]
    try:
        for source, opener in sources:
            for attempt in (1, 2):
                try:
                    record['counts'][source] = result = collect_source(driver, source, opener, args, key, out)
                    print(source, *result.values(), sep='\t', flush=True)
                    break
                except Stop:
                    raise
                except (InvalidSessionIdException, WebDriverException) as error:
                    lost = isinstance(error, InvalidSessionIdException) or 'disconnected' in str(error) or 'not connected' in str(error)
                    if not lost:
                        record['errors'].append(f'{source}: {type(error).__name__}: {str(error)[:200]}')
                        print(source, 'error', type(error).__name__, sep='\t', flush=True)
                        break
                    if attempt == 2:
                        raise Stop(f'lost the browser tab twice on {source}; is the Brave window still open?')
                    try:
                        driver.quit()
                    except WebDriverException:
                        pass
                    pause(3, 6)
                    driver = attach()  # the tab can switch renderer processes on heavy pages; reattach and retry once
                except Exception as error:  # one source does not stop the others
                    record['errors'].append(f'{source}: {type(error).__name__}: {str(error)[:200]}')
                    print(source, 'error', type(error).__name__, sep='\t', flush=True)
                    break
    except Stop as error:
        record['errors'].append(f'stopped: {error}')
        raise
    finally:
        record['finished_at'] = now_utc()
        path = out / '_run.json'
        runs = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        path.write_text(json.dumps(runs + [record], ensure_ascii=False, indent=1), encoding='utf-8')
    return 1 if record['errors'] else 0


def parse_communities(html, query):
    rows = []
    for item in BeautifulSoup(html, 'html.parser').select('[data-testid="group_item_desktop_list"]'):
        link = item.select_one('a[href]')
        texts = list(item.stripped_strings)
        members = next((t for t in texts if re.search(r'подписчик|участник', t)), None)
        rows.append(dict(id=link['href'].split('?')[0].strip('/') if link else None, query=query,
                         name=texts[0] if texts else None, kind=texts[1] if len(texts) > 1 else None,
                         members=number(re.sub(r'\D', '', members or '')), members_raw=members, _collected_at=now_utc()))
    return [r for r in rows if r['id']]


def cmd_communities(args, driver):
    if not logged_in(driver)[0]:
        raise Stop('not logged in: log in in the browser window')
    found = []
    for query in args.query:
        pause()
        driver.get('https://vk.ru/search/communities?q=' + query)
        pause(3, 6)
        check(driver)
        found += scroll_and_collect(driver, lambda html, q=query: parse_communities(html, q), max_items=20)
    write_jsonl(out_dir() / f'communities_{datetime.now(timezone.utc).strftime("%H%M%S")}.jsonl', found)
    for row in found:
        print(row['query'], row['id'], row['members'], row['kind'], row['name'], sep='\t')


def cmd_close(args):
    if not STATE.exists():
        print('No browser registered')
        return 0
    state = json.loads(STATE.read_text())
    try:
        signal_group = __import__('os').getpgid(state['pid'])
        __import__('os').killpg(signal_group, signal.SIGTERM)
    except ProcessLookupError:
        pass
    time.sleep(2)
    shutil.rmtree(state['profile'], ignore_errors=True)
    STATE.unlink()
    print('Browser closed, temporary profile deleted')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    p_browser = commands.add_parser('browser', help='open the browser for login')
    p_browser.add_argument('--browser', choices=sorted(BROWSERS), default='brave')
    commands.add_parser('status', help='check login')
    p_snapshot = commands.add_parser('snapshot', help='save pages for the pilot')
    p_snapshot.add_argument('--url', action='append', help=f'repeatable; default: {DEFAULT_SNAPSHOTS}')
    p_snapshot.add_argument('--scrolls', type=int, default=3, help='scroll steps per page (default: 3)')
    p_collect = commands.add_parser('collect', help='collect posts and comments')
    p_collect.add_argument('--term', default='Электрозавод', help='search word (default: Электрозавод)')
    p_collect.add_argument('--community', action='append', help=f'community slug; repeatable; default: {DEFAULT_COMMUNITIES}')
    p_collect.add_argument('--no-global', action='store_true', help='skip the global post search')
    p_collect.add_argument('--since', default='2025-09-01', help='open comments only for posts on or after this date')
    p_collect.add_argument('--max-posts', type=int, default=300, help='stop scrolling a result list at this many posts')
    p_collect.add_argument('--max-comment-posts', type=int, help='open comments under at most N posts per source; pilot')
    p_collect.add_argument('--tag', help='added to output file names, for a repeat run on the same day')
    p_communities = commands.add_parser('communities', help='find communities by name; prints slug, members, name')
    p_communities.add_argument('--query', action='append', required=True, help='repeatable')
    commands.add_parser('close', help='close the browser and delete its profile')
    args = parser.parse_args()
    if args.command in ('browser', 'close'):
        return (cmd_browser if args.command == 'browser' else cmd_close)(args) or 0
    driver = attach()  # quit() below stops the driver only; the attached browser stays open
    try:
        return {'status': cmd_status, 'snapshot': cmd_snapshot, 'collect': cmd_collect,
                'communities': cmd_communities}[args.command](args, driver) or 0
    except Stop as error:
        print(f'stopped: {error}. Act in the browser window, then run again.', file=sys.stderr)
        return 1
    finally:
        driver.quit()


if __name__ == '__main__':
    sys.exit(main())
