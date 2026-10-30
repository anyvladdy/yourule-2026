"""Count the report's characters with spaces against the 10,000 limit (AGENTS §2).

Run from the repository root: .venv/bin/python src/report/check_length.py
Takes the text between <!-- text --> and <!-- /text --> in deliverables/drafts/s0_*.md … s7_*.md, in that order,
headings included. Appendices (appendix_*.md) are outside the limit and are only listed. Page count is checked on the
.docx later; here a rough estimate assumes 1,800 characters per page of Times New Roman 12 with single spacing.
Exit code 1 if the total is over the limit or a section is missing or has no marked text.
This is the drafts count. The Word file adds section numbers and the figure caption: the final count is the one
printed by src/report/build_docx.py (with and without paragraph breaks).
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRAFTS = ROOT / 'deliverables/drafts'
TEXT = re.compile(r'<!-- text -->\n(.*?)<!-- /text -->', re.S)


def section_text(path):
    match = TEXT.search(path.read_text(encoding='utf-8'))
    if not match:
        return ''
    # Markdown markers are not printed in the report: heading hashes, list numbers stay, emphasis marks go.
    text = re.sub(r'^#+\s*', '', match.group(1), flags=re.M)
    return re.sub(r'\*\*|__', '', text).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--limit', type=int, default=10_000, help='characters with spaces (default 10,000)')
    args = parser.parse_args()
    total = 0
    missing = []
    for number in range(8):
        files = sorted(DRAFTS.glob(f's{number}_*.md'))
        if not files:
            print(f's{number}: missing')
            missing.append(f's{number}')
            continue
        # paragraphs are joined by one line break in the document, so blank lines count once
        text = re.sub(r'\n{2,}', '\n', section_text(files[0]))
        if not text:
            print(f'{files[0].name}: no text between the markers')
            missing.append(files[0].name)
            continue
        total += len(text)
        print(f'{files[0].name:28s} {len(text):6,}')
    for path in sorted(DRAFTS.glob('appendix_*.md')):
        print(f'{path.name:28s} {len(section_text(path)):6,}  (appendix, outside the limit)')
    print(f'total {total:,} of {args.limit:,} characters with spaces; about {total / 1800:.1f} pages')
    if missing:
        print('incomplete: ' + ', '.join(missing))
    return 1 if total > args.limit or missing else 0


if __name__ == '__main__':
    sys.exit(main())
