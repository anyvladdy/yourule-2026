"""Throwaway probe: can headless Chrome open Dzen search without login? Prints what it sees.

Run from the repo root: .venv/bin/python workflow/stage1/T16_dzen/probe_dzen.py [--query ...]
Dumps page source into workflow/stage1/T16_dzen/out/_probe/ for inspection (not raw data).
"""
import argparse
import re
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', default='Электрозавод')
    parser.add_argument('--url', help='open this URL instead of search')
    parser.add_argument('--wait', type=float, default=6.0)
    args = parser.parse_args()

    url = args.url or f'https://dzen.ru/search?query={args.query}'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1400,1400')
    options.add_argument('--lang=ru-RU')
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    try:
        driver.get(url)
        import time
        time.sleep(args.wait)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(args.wait / 2)
        html = driver.page_source
        out = Path(__file__).resolve().parent / 'out' / '_probe'
        out.mkdir(parents=True, exist_ok=True)
        (out / 'page.html').write_text(html, encoding='utf-8')
        print('url:', driver.current_url)
        print('title:', driver.title)
        print('len:', len(html))
        for marker in ['captcha', 'SmartCaptcha', 'Авториз', 'Войдите', 'войти', 'robot', 'Вход']:
            if marker.lower() in html.lower():
                print('marker:', marker)
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
        hrefs = [a.get_attribute('href') for a in links]
        print('links:', len(hrefs))
        for h in hrefs[:60]:
            print('  ', h)
        print('cards:', re.findall(r'class="[^"]*card[^"]*"', html)[:10])
    finally:
        driver.quit()


if __name__ == '__main__':
    sys.exit(main())
