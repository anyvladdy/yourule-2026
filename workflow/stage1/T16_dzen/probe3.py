"""Throwaway probe 3: expand every reply and 'show more' in a Dzen article's comments, dump the DOM.

Run from the repo root: .venv/bin/python workflow/stage1/T16_dzen/probe3.py <url> [--clicks N]
Brave, headless, incognito, throwaway profile deleted at exit.
"""
import argparse, random, re, sys, tempfile, time
from pathlib import Path
from selenium import webdriver
from bs4 import BeautifulSoup

BRAVE = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
OUT = Path(__file__).resolve().parent / 'out' / '_probe'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url')
    ap.add_argument('--clicks', type=int, default=25)
    ap.add_argument('--name', default='comments_expanded')
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.TemporaryDirectory(prefix='dz_')
    o = webdriver.ChromeOptions()
    o.binary_location = BRAVE
    for flag in ('--headless=new', '--incognito', f'--user-data-dir={tmp.name}', '--no-first-run',
                 '--disable-gpu', '--no-sandbox', '--window-size=1400,1800', '--lang=ru-RU'):
        o.add_argument(flag)
    d = webdriver.Chrome(options=o)
    d.set_page_load_timeout(60)
    try:
        d.get(args.url)
        time.sleep(random.uniform(3, 5))
        for _ in range(14):
            d.execute_script(f'window.scrollBy(0, Math.round(window.innerHeight * {0.7 + random.random() * 0.3:.2f}))')
            time.sleep(random.uniform(1.5, 3.0))
        for step in range(args.clicks):
            hit = 0
            for b in d.find_elements('css selector', 'button'):
                try:
                    label = b.text.strip()
                except Exception:
                    continue
                if re.match(r'^(\d+\s+ответ|\d+\s+ответа|\d+\s+ответов|Ещё\s+\d+\s+коммент)', label) and b.is_displayed():
                    d.execute_script('arguments[0].scrollIntoView({block:"center"}); arguments[0].click();', b)
                    hit += 1
                    time.sleep(random.uniform(1.2, 2.5))
            print('step', step, 'clicked', hit, flush=True)
            if not hit:
                break
        time.sleep(2)
        html = d.page_source
        (OUT / f'{args.name}.html').write_text(html, encoding='utf-8')
        s = BeautifulSoup(html, 'html.parser')
        sec = s.select_one('[data-testid="article-comments"]')
        counter = sec.select_one('[data-testid="comments-header-counter-text"]')
        print('counter:', counter.get_text(strip=True) if counter else None)
        print('testids:', sorted({t.get('data-testid') for t in sec.select('[data-testid]')}))
        print('nested comment wrappers:', len(sec.select('[class*="comment__wrapper"]')))
        print('root:', len(sec.select('[data-testid="root-comment"]')))
    finally:
        d.quit()
        tmp.cleanup()


if __name__ == '__main__':
    sys.exit(main())
