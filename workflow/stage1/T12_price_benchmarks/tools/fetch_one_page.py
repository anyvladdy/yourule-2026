#!/usr/bin/env python3
"""Open one public page and print a text window around a search pattern.

Helper for reading price pages by hand without pasting whole pages into the
session. One URL per run, reader pace, no crawling.
"""
import argparse
import gzip
import html
import io
import re
import sys
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ru,en"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        enc = resp.headers.get("Content-Encoding", "")
    if enc == "gzip":
        raw = gzip.decompress(raw)
    charset = "utf-8"
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:4000])
    if m:
        charset = m.group(1).decode("ascii", "ignore")
    try:
        return raw.decode(charset, "replace")
    except LookupError:
        return raw.decode("utf-8", "replace")


def text_of(page: str) -> str:
    page = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?is)<br\s*/?>|</(p|div|tr|li|h[1-6]|td|th)>", "\n", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    page = html.unescape(page)
    page = re.sub(r"[ \t\xa0]+", " ", page)
    page = re.sub(r"\n\s*\n+", "\n", page)
    return page


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--find", default=None, help="regex; print windows around matches")
    ap.add_argument("--window", type=int, default=240)
    ap.add_argument("--max", type=int, default=6, help="max windows")
    ap.add_argument("--head", type=int, default=0, help="print first N chars instead")
    ap.add_argument("--title", action="store_true", help="print page title only")
    args = ap.parse_args()

    page = get(args.url)
    if args.title:
        m = re.search(r"(?is)<title>(.*?)</title>", page)
        print(html.unescape(m.group(1)).strip() if m else "(no title)")
        return 0
    txt = text_of(page)
    if args.head:
        print(txt[: args.head])
        return 0
    if not args.find:
        print(txt[:4000])
        return 0
    shown = 0
    for m in re.finditer(args.find, txt, re.I):
        start = max(0, m.start() - args.window // 2)
        end = min(len(txt), m.end() + args.window)
        print("---")
        print(txt[start:end].replace("\n", " | "))
        shown += 1
        if shown >= args.max:
            break
    if not shown:
        print("no match for %r" % args.find)
    return 0


if __name__ == "__main__":
    sys.exit(main())
