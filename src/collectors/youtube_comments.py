"""Collect YouTube videos and their comments through the official Data API v3 (D-19).

Run from the repository root. Needs YOUTUBE_API_KEY in .env or in the environment.
Raw API items go to data/raw/youtube/<YYYY-MM-DD>/ as JSONL, each line with _collected_at;
every run is appended to _run.json there, with requests counted per API method. Existing files are never overwritten.

  search    find videos by query; saves search hits and video metadata, prints a list to choose from
  comments  saves all comment threads with all replies for the given videos, plus metadata for --video ids

Per-video status: complete_for_run (all pages the API returned), limited (--max-pages pilot), disabled,
partial (stopped by an error; pages received so far are kept in comments_<id>_partial_<time>.jsonl), failed.
Quota: search.list and the other methods have separate daily limits; check them in the project's Cloud Console.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'youtube_comments/0.2'
API = 'https://www.googleapis.com/youtube/v3/'
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUERIES = ['Электрозавод снос', 'Электрозавод Эталон', 'Электрозавод редевелопмент', 'сохранить Электрозавод']
REQUESTS = Counter()


class ApiError(Exception):
    def __init__(self, code, reasons, message=''):
        super().__init__(f'HTTP {code}: {", ".join(sorted(reasons)) or "no reason given"} {message}'.strip())
        self.reasons = reasons
        self.partial = {}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def stamp():
    return datetime.now(timezone.utc).strftime('%H%M%S')


def api_key():
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            name, _, value = line.partition('=')
            value = value.strip().strip('"\'')
            if name.strip() == 'YOUTUBE_API_KEY' and value:
                os.environ.setdefault('YOUTUBE_API_KEY', value)
    if not os.environ.get('YOUTUBE_API_KEY'):
        sys.exit('YOUTUBE_API_KEY is not set: copy .env.example to .env and fill it in')
    return os.environ['YOUTUBE_API_KEY']


def call(method, params, key):
    url = API + method + '?' + urllib.parse.urlencode({**params, 'key': key})
    for attempt in range(4):
        REQUESTS[method] += 1
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            try:
                body = json.loads(error.read() or b'{}')
            except ValueError:
                body = {}
            reasons = {e.get('reason', '') for e in body.get('error', {}).get('errors', [])}
            if error.code < 500 and error.code != 429:
                raise ApiError(error.code, reasons, body.get('error', {}).get('message', ''))
        except urllib.error.URLError:
            pass
        time.sleep(2 ** attempt)
    raise ApiError(0, {'no_response_after_4_attempts'})


def pages(method, params, key, max_pages=None):
    token, count = None, 0
    while True:
        data = call(method, {**params, **({'pageToken': token} if token else {})}, key)
        yield data
        count += 1
        token = data.get('nextPageToken')
        if not token or (max_pages and count >= max_pages):
            return


def video_id(value):
    match = re.search(r'(?:v=|youtu\.be/|/live/|/shorts/)([\w-]{11})', value)
    return match.group(1) if match else value


def write_jsonl(path, items):
    with path.open('x', encoding='utf-8') as stream:
        for item in items:
            stream.write(json.dumps(item, ensure_ascii=False) + '\n')


def log_run(out, record):
    path = out / '_run.json'
    runs = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    path.write_text(json.dumps(runs + [record], ensure_ascii=False, indent=1), encoding='utf-8')


def fetch_videos(ids, key):
    videos = []
    for start in range(0, len(ids), 50):
        data = call('videos', {'part': 'snippet,statistics,contentDetails,liveStreamingDetails',
                               'id': ','.join(ids[start:start + 50])}, key)
        videos += [{**item, '_collected_at': now()} for item in data.get('items', [])]
    return videos


def search(args, key, out, record):
    run = stamp()
    hits = []
    for query in args.query or DEFAULT_QUERIES:
        params = {'part': 'snippet', 'type': 'video', 'q': query, 'maxResults': 50, 'order': 'relevance',
                  'regionCode': 'RU', 'relevanceLanguage': 'ru', 'publishedAfter': args.after + 'T00:00:00Z'}
        for page in pages('search', params, key, args.pages):
            hits += [{**item, '_query': query, '_collected_at': now()} for item in page.get('items', [])]
    write_jsonl(out / f'search_{run}.jsonl', hits)
    videos = fetch_videos(list(dict.fromkeys(hit['id']['videoId'] for hit in hits)), key)
    write_jsonl(out / f'videos_{run}.jsonl', videos)
    record['counts'] = {'search_hits': len(hits), 'unique_videos': len(videos)}
    record['files'] = [f'search_{run}.jsonl', f'videos_{run}.jsonl']
    for video in sorted(videos, key=lambda v: -int(v['statistics'].get('commentCount', 0))):
        print(video['id'], video['snippet']['publishedAt'][:10], video['statistics'].get('commentCount', '-'),
              video['snippet']['channelTitle'], '|', video['snippet']['title'], sep='\t')


def collect_comments(video, key, out, max_pages):
    path = out / f'comments_{video}{f"_pilot{max_pages}" if max_pages else ""}.jsonl'
    if path.exists():
        return {'status': 'skipped_exists'}
    part = path.with_name(path.name + '.part')
    counts = {'threads': 0, 'replies': 0}
    try:
        with part.open('w', encoding='utf-8') as stream:
            params = {'part': 'snippet,replies', 'videoId': video, 'maxResults': 100, 'textFormat': 'plainText'}
            for page in pages('commentThreads', params, key, max_pages):
                for thread in page.get('items', []):
                    shown = thread.get('replies', {}).get('comments', [])
                    if thread['snippet']['totalReplyCount'] > len(shown):
                        parent = thread['snippet']['topLevelComment']['id']
                        params_r = {'part': 'snippet', 'parentId': parent, 'maxResults': 100, 'textFormat': 'plainText'}
                        thread['replies'] = {'comments': [c for p in pages('comments', params_r, key) for c in p.get('items', [])]}
                    stream.write(json.dumps({**thread, '_collected_at': now()}, ensure_ascii=False) + '\n')
                    counts['threads'] += 1
                    counts['replies'] += len(thread.get('replies', {}).get('comments', []))
    except ApiError as error:
        if 'commentsDisabled' in error.reasons:
            part.unlink(missing_ok=True)
            return {'status': 'disabled'}
        if counts['threads']:
            part.rename(path.with_name(f'{path.stem}_partial_{stamp()}.jsonl'))
        else:
            part.unlink(missing_ok=True)
        error.partial = counts
        raise
    part.rename(path)
    return {'status': 'limited' if max_pages else 'complete_for_run', **counts}


def comments(args, key, out, record):
    ids = [video_id(v) for v in args.video or []]
    if ids:
        name = f'videos_{stamp()}.jsonl'
        write_jsonl(out / name, fetch_videos(ids, key))
        record['files'] = [name]
    if args.from_videos:
        for line in Path(args.from_videos).read_text(encoding='utf-8').splitlines():
            item = json.loads(line)
            text = item['snippet']['title'] + '\n' + item['snippet'].get('description', '')
            if (int(item['statistics'].get('commentCount', 0)) >= args.min_comments
                    and (not args.match or re.search(args.match, text, re.IGNORECASE))
                    and item['snippet']['channelTitle'] not in (args.skip_channel or [])):
                ids.append(item['id'])
    ids = list(dict.fromkeys(ids))
    record['params']['videos'] = ids
    record['counts'] = {}
    for video in ids:
        try:
            result = collect_comments(video, key, out, args.max_pages)
        except ApiError as error:
            result = {'status': 'partial' if error.partial.get('threads') else 'failed', **error.partial, 'error': str(error)}
            record['errors'].append(f'{video}: {error}')
            record['counts'][video] = result
            print(video, *result.values(), sep='\t')
            if error.reasons & {'quotaExceeded', 'dailyLimitExceeded'}:
                break
            continue
        record['counts'][video] = result
        print(video, *result.values(), sep='\t')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    p_search = commands.add_parser('search', help='find videos by query')
    p_search.add_argument('--query', action='append', help=f'repeatable; default: {DEFAULT_QUERIES}')
    p_search.add_argument('--after', default='2025-01-01', help='published on or after, YYYY-MM-DD (default: 2025-01-01)')
    p_search.add_argument('--pages', type=int, default=1, help='result pages of 50 per query (default: 1)')
    p_comments = commands.add_parser('comments', help='save comments for videos')
    p_comments.add_argument('--video', action='append', help='video id or URL; repeatable; its metadata is saved too')
    p_comments.add_argument('--from-videos', help='videos_*.jsonl from a search run: take all its videos')
    p_comments.add_argument('--min-comments', type=int, default=1, help='with --from-videos: skip videos with fewer comments')
    p_comments.add_argument('--match', help='with --from-videos: keep a video only if this regex matches its title or description')
    p_comments.add_argument('--skip-channel', action='append', help='with --from-videos: channel title to skip; repeatable')
    p_comments.add_argument('--max-pages', type=int, help='top-level comment pages of 100 per video; for pilots')
    args = parser.parse_args()
    if args.command == 'comments' and not (args.video or args.from_videos):
        parser.error('comments needs --video or --from-videos')

    key = api_key()
    out = ROOT / 'data/raw/youtube' / datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out.mkdir(parents=True, exist_ok=True)
    record = {'command': args.command, 'collector_version': VERSION, 'started_at': now(),
              'params': {k: v for k, v in vars(args).items() if k != 'command'}, 'errors': []}
    try:
        (search if args.command == 'search' else comments)(args, key, out, record)
    except ApiError as error:
        record['errors'].append(str(error))
        print(f'stopped: {error}', file=sys.stderr)
    finally:
        record['requests'] = dict(REQUESTS)
        record['finished_at'] = now()
        log_run(out, record)
    return 1 if record['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
