"""Collect the signature list of the Archi.ru open letter on Электрозавод (P01), without signers' names (D-42).

Run from the repository root: .venv/bin/python src/collectors/archi_petition.py
The list is public: https://archi.ru/files/misc/inquiry/19/ shows 200 signatures per page, newest first, pages by
`index.php?offset=N`. Plain HTTP requests get 403 from the host's protection, so pages are read in headless Chrome
with a clean incognito profile at reader pace (random pause before every page). A block page or a captcha stops the
run; it is not worked around (AGENTS §3). The run prints the offset to resume from.

Each signature line is «<n>. <name>[, <occupation>], DD.MM.YYYY HH:MM:SS» with an optional comment below. The name
is dropped while parsing and never stored. Kept: number, self-described occupation, time (Moscow), comment.
Output in data/raw/petitions/<YYYY-MM-DD>/: archi_signatures.jsonl (one row per signature) and _run.json.
Offsets already in the output are skipped, so an interrupted run can be restarted with the same command.
"""
import argparse
import json
import random
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bs4 import BeautifulSoup

VERSION = 'archi_petition/0.1'
ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://archi.ru/files/misc/inquiry/19/'
PAGE = 200
MSK = timezone(timedelta(hours=3))
LINE = re.compile(r'^(\d+)\.\s*(.*?),\s*(\d\d\.\d\d\.\d{4} \d\d:\d\d:\d\d)\s*$', re.S)
BLOCKED = re.compile(r'access denied|captcha|не робот|подтвердите, что вы', re.I)


class Stop(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def parse(html, offset):
    """Signatures on one page; the name (first comma-separated part) is dropped here."""
    soup = BeautifulSoup(html, 'html.parser')
    total = re.search(r'подписались:\s*(\d+)', soup.get_text(' '))
    rows = []
    for head in soup.select('p.txt5'):
        match = LINE.match(' '.join(head.get_text(' ').split()))
        if not match:
            continue
        number, who, stamp = match.groups()
        parts = [part.strip() for part in who.split(',')]
        occupation = ', '.join(parts[1:]).strip() or None  # parts[0] is the name: not kept
        body = head.find_next_sibling('p', class_='txt6')
        comment = body.get_text('\n').strip() if body else ''
        signed = datetime.strptime(stamp, '%d.%m.%Y %H:%M:%S').replace(tzinfo=MSK)
        rows.append({'sig_id': int(number), 'occupation': occupation, 'signed_at_msk': signed.isoformat(),
                     'signed_at_utc': signed.astimezone(timezone.utc).isoformat(), 'comment': comment or None,
                     'offset': offset, 'collected_at': now(), 'collector_version': VERSION})
    return rows, int(total.group(1)) if total else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--start', type=int, default=0, help='first offset (default 0, the newest page)')
    parser.add_argument('--stop', type=int, help='last offset, inclusive (default: the last page)')
    parser.add_argument('--step', type=int, default=PAGE, help='offset step; 2000 reads every 10th page (default 200)')
    parser.add_argument('--pause', type=float, nargs=2, default=(8.0, 15.0), metavar=('MIN', 'MAX'),
                        help='random pause before each page, seconds (default 8 15)')
    parser.add_argument('--date', default=datetime.now(MSK).strftime('%Y-%m-%d'), help='output folder date')
    args = parser.parse_args()

    out = ROOT / 'data/raw/petitions' / args.date
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'archi_signatures.jsonl'
    done = {json.loads(line)['offset'] for line in path.open(encoding='utf-8')} if path.exists() else set()
    record = {'version': VERSION, 'started': now(), 'params': vars(args), 'pages': 0, 'signatures': 0,
              'total_shown': None, 'stopped': None, 'errors': []}

    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException
    options = webdriver.ChromeOptions()
    for flag in ('--headless=new', '--incognito', '--window-size=1200,1000'):
        options.add_argument(flag)
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    try:
        offset = args.start
        while True:
            if args.stop is not None and offset > args.stop:
                break
            if offset in done:
                offset += args.step
                continue
            time.sleep(random.uniform(*args.pause))
            # A network error or a page that does not load is tried again up to 3 times with longer pauses;
            # a block page is not an error and is never retried.
            for attempt in range(4):
                try:
                    driver.get(BASE if offset == 0 else f'{BASE}index.php?offset={offset}')
                    break
                except WebDriverException as error:
                    if attempt == 3:
                        raise
                    print(f'offset {offset}: {type(error).__name__}, retry {attempt + 1} of 3', flush=True)
                    time.sleep(30 * (attempt + 1))
            time.sleep(random.uniform(1.5, 3.0))  # let the page settle, as a reader would
            html = driver.page_source
            if BLOCKED.search(html[:5000]) or BLOCKED.search(driver.title or ''):
                raise Stop(f'block or captcha at offset {offset}')
            rows, total = parse(html, offset)
            record['total_shown'] = total or record['total_shown']
            if not rows:
                if total is not None and offset >= total:
                    break  # past the last page
                raise Stop(f'no signatures parsed at offset {offset}')
            with path.open('a', encoding='utf-8') as stream:
                for row in rows:
                    stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            record['pages'] += 1
            record['signatures'] += len(rows)
            print(f'offset {offset}: {len(rows)} signatures, ids {rows[-1]["sig_id"]}–{rows[0]["sig_id"]}', flush=True)
            offset += args.step
    except Stop as error:
        record['stopped'] = str(error)
        print(f'STOPPED: {error}. Resume later with --start {offset}', flush=True)
    except Exception as error:
        record['errors'].append(f'{type(error).__name__}: {error}')
        print(f'error at offset {offset}: {error}. Resume with --start {offset}', flush=True)
    finally:
        driver.quit()
        record['finished'] = now()
        runs_path = out / '_run.json'
        runs = json.loads(runs_path.read_text(encoding='utf-8')) if runs_path.exists() else []
        runs_path.write_text(json.dumps(runs + [record], ensure_ascii=False, indent=1), encoding='utf-8')
    # Exit 2: stopped by a block or captcha (ask the user); 1: other error (safe to resume); 0: done.
    return 2 if record['stopped'] else 1 if record['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
