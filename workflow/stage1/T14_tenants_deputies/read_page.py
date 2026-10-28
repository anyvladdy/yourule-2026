"""Read a few public pages in Google Chrome without a visible window (headless), at a human pace.

  python workflow/stage1/T14_tenants_deputies/read_page.py URL [URL ...] [--chars 4000]
  python workflow/stage1/T14_tenants_deputies/read_page.py --verify
  python workflow/stage1/T14_tenants_deputies/read_page.py --close

It is a reader, not a collector: it opens the URLs given on the command line, one at a time, in one tab, and saves
the visible text for reading. Nothing is crawled, no links are followed.

To look like an ordinary visit rather than a burst: the tab is sized like a laptop screen, the page is scrolled in a
few short steps with pauses, the mouse moves a little, and each page gets a random wait before the text is read.
A captcha, a "too many requests" page or a login wall stops the run and is reported, never worked around.

Full text: workflow/stage1/T14_tenants_deputies/out/pages/<slug>.txt
"""
import argparse
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
PAGES = HERE / 'out' / 'pages'
BINARY = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
PROFILE = Path(__file__).resolve().parents[3] / '.tmp' / 'chrome-t14'
WALLS = ('Подтвердите, что вы не робот', 'Слишком много запросов', 'Too many requests',
         'unusual traffic', 'Access denied', 'Доступ ограничен')
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/156.0.0.0 Safari/537.36')


def slug(url):
    p = urlparse(url)
    s = re.sub(r'[^a-zA-Z0-9]+', '-', (p.netloc + p.path).strip('/')).strip('-')
    return (s[:80] or 'page').lower()


def new_driver():
    from selenium import webdriver
    options = webdriver.ChromeOptions()
    options.binary_location = BINARY
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1440,900')
    options.add_argument('--lang=ru-RU')
    options.add_argument(f'--user-agent={UA}')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-breakpad')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    # Chrome's own sandbox cannot start inside the workspace sandbox; the profile is throwaway and local.
    options.add_argument('--no-sandbox')
    options.add_argument(f'--user-data-dir={PROFILE}')
    options.page_load_strategy = 'eager'  # heavy pages often never fire "load"; we read what is rendered
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)
    return driver


def pause(lo=1.0, hi=2.5):
    time.sleep(random.uniform(lo, hi))


def human_browse(driver):
    """Small, irregular movements: a few wheel-less scroll steps with pauses, a couple of mouse moves."""
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    height = driver.execute_script('return document.body ? document.body.scrollHeight : 0') or 0
    steps = random.randint(3, 6)
    for _ in range(steps):
        driver.execute_script('window.scrollBy(0, Math.round(window.innerHeight * %f));' % random.uniform(0.5, 0.9))
        pause(0.6, 1.8)
        if height and driver.execute_script('return window.scrollY + window.innerHeight') >= height - 50:
            break
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        ActionChains(driver).move_to_element_with_offset(
            body, random.randint(40, 300), random.randint(40, 200)).perform()
    except Exception:  # noqa: BLE001 - a decorative step, never fatal
        pass
    driver.execute_script('window.scrollTo(0, 0);')
    pause(0.5, 1.2)


def check(driver):
    text = driver.execute_script('return document.body ? document.body.innerText : ""')
    hit = next((w for w in WALLS if w.lower() in text.lower()), None)
    if hit:
        raise SystemExit(f'STOP: "{hit}" on {driver.current_url}. The page refused the visit; not worked around.')
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('urls', nargs='*')
    ap.add_argument('--chars', type=int, default=4000)
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--close', action='store_true')
    args = ap.parse_args()
    if not args.urls and not (args.verify or args.close):
        ap.error('give URLs, or --verify / --close')

    driver = new_driver()
    try:
        if args.verify:
            caps = driver.capabilities
            driver.get('data:text/html,<h1>ok</h1>')
            print(json.dumps({'browserName': caps.get('browserName'), 'browserVersion': caps.get('browserVersion'),
                              'headless_args': [a for a in (driver.capabilities.get('goog:chromeOptions', {})
                                                            .get('args', [])) if 'headless' in a],
                              'ua': driver.execute_script('return navigator.userAgent')}, ensure_ascii=False, indent=1))
        PAGES.mkdir(parents=True, exist_ok=True)
        for url in args.urls:
            try:
                driver.get(url)
            except Exception as exc:  # noqa: BLE001 - a slow page is not a dead end: read what arrived
                print(f'\n=== {url}\nSLOW LOAD ({type(exc).__name__}), reading what is rendered')
            for _ in range(40):
                if driver.execute_script('return document.readyState') == 'complete':
                    break
                time.sleep(0.25)
            pause(1.5, 3.0)
            human_browse(driver)
            pause(1.0, 2.5)
            text = check(driver)
            title, final_url = driver.title, driver.current_url
            path = PAGES / f'{slug(url)}.txt'
            path.write_text(f'URL: {url}\nFINAL: {final_url}\nTITLE: {title}\n\n{text}', encoding='utf-8')
            print(f'\n=== {url}\nTITLE: {title}\nCHARS: {len(text)}\nSAVED: {path.relative_to(HERE)}\n')
            print(text[:args.chars])
            pause(2.0, 5.0)
    finally:
        if args.close:
            driver.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main())
