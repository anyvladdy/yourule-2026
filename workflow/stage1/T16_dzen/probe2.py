"""Throwaway probe 2: open given Dzen pages, scroll to the comments, report what the DOM shows.

Run from the repo root: .venv/bin/python workflow/stage1/T16_dzen/probe2.py <url> [<url> ...]
Saves each page source into out/_probe/ for selector work. Not raw data.
"""
import random
import re
import sys
import time
from pathlib import Path

from selenium import webdriver

BRAVE = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
OUT = Path(__file__).resolve().parent / 'out' / '_probe'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.binary_location = BRAVE
    options.add_argument('--headless=new')
    options.add_argument('--incognito')
    import tempfile
    options.add_argument(f'--user-data-dir={tempfile.mkdtemp(prefix="dz_")}')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1400,1600')
    options.add_argument('--lang=ru-RU')
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    try:
        for index, url in enumerate(sys.argv[1:]):
            driver.get(url)
            time.sleep(random.uniform(2, 5))
            for _ in range(14):
                driver.execute_script('window.scrollBy(0, Math.round(window.innerHeight * (0.7 + Math.random() * 0.3)))')
                time.sleep(random.uniform(1.5, 3.5))
            text = driver.execute_script('return document.body.innerText')
            name = re.sub(r'\W+', '_', url)[-60:]
            (OUT / f'p2_{index}_{name}.html').write_text(driver.page_source, encoding='utf-8')
            print('=' * 70)
            print(url)
            print('title:', driver.title[:120])
            head = re.search(r'Комментари[^\n]*\n?(.{0,80})', text)
            print('comments area:', repr(head.group(0)[:160]) if head else 'no Комментарии block')
            print('auth wall:', 'Войти, чтобы комментировать' in text)
            testids = sorted(set(re.findall(r'data-testid="([^"]+)"', driver.page_source)))
            print('comment testids:', [t for t in testids if 'comment' in t.lower()])
    finally:
        driver.quit()


if __name__ == '__main__':
    sys.exit(main())
