"""Collect public VK posts and comments about Электрозавод in a browser where the user logs in by hand (D-21).

Run from the repository root.

  browser   open Brave in incognito with a fresh temporary profile at the VK login page; log in there yourself
  status    check that the browser is reachable and logged in (prints cookie names only, never values)
  snapshot  pilot: open the given URLs, scroll at reader pace, save the page HTML to check selectors before collecting
  close     close that Brave window and delete its temporary profile

Every command after `browser` attaches to the same window through a local debugging port, so you log in once.
The port listens on 127.0.0.1 only; run `close` when the collection is over.
Reader pace: random pauses and slow scrolling. A captcha, a "too many requests" page or a logout stops the run and
asks you to act; it is never worked around (AGENTS §3). Raw pages go to data/raw/vk/<YYYY-MM-DD>/ (not in git).
"""
import argparse
import json
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.secrets' / 'vk_browser.json'
BROWSERS = {'brave': '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
            'chrome': '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}
PORT = 9222
SESSION_COOKIES = ('remixsid', 'remixnsid')
WALLS = ('captcha', 'Подтвердите, что вы не робот', 'Слишком много запросов', 'Too many requests')
DEFAULT_SNAPSHOTS = ['https://vk.com/search/statuses?q=Электрозавод',
                     'https://vk.com/search?c%5Bq%5D=Электрозавод&c%5Bsection%5D=statuses',
                     'https://vk.com/sokgor']


class Stop(Exception):
    """VK showed a captcha, a limit or a logout: the user has to act."""


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
    source = driver.page_source
    hit = next((w for w in WALLS if w in source), None)
    if hit:
        raise Stop(f'"{hit}" on {driver.current_url}')
    if 'vk.com/login' in driver.current_url or 'id.vk.com' in driver.current_url:
        raise Stop(f'not logged in: {driver.current_url}')


def logged_in(driver):
    if 'vk.com' not in driver.current_url:
        driver.get('https://vk.com/feed')
        pause(2, 4)
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
    commands.add_parser('close', help='close the browser and delete its profile')
    args = parser.parse_args()
    if args.command in ('browser', 'close'):
        return (cmd_browser if args.command == 'browser' else cmd_close)(args) or 0
    driver = attach()  # quit() below stops the driver only; the attached browser stays open
    try:
        return {'status': cmd_status, 'snapshot': cmd_snapshot}[args.command](args, driver) or 0
    except Stop as error:
        print(f'stopped: {error}. Act in the browser window, then run again.', file=sys.stderr)
        return 1
    finally:
        driver.quit()


if __name__ == '__main__':
    sys.exit(main())
