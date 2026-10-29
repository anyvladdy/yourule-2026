"""Build the report as a Word file from the drafts: title page, sections s0–s7 with figure 1, appendices А–Ж.

Run from the repository root after build_appendices.py:
.venv/bin/python src/report/build_docx.py                → deliverables/Elektrozavod_report.docx
.venv/bin/python src/report/build_docx.py --main-only    → title page and main text only (for the page check)
Only the text between <!-- text --> marks is used. Supported markup: "## " heading, paragraphs, "1. " list items,
"**whole line**" in bold, pipe tables, [[figure:path|caption|max height cm]], [[pagebreak]]. Times New Roman 12 for the text (line spacing 1.15 in the main text), 9 in wide tables.
Prints the character count of the main text with spaces (title page and appendices excluded).
"""
import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DRAFTS = ROOT / 'deliverables/drafts'
MAIN = ['s0_summary', 's1_situation', 's2_image_concept', 's3_audiences', 's4_strategy', 's5_negative',
        's6_budget', 's7_plan']
# (draft, landscape)
APPENDICES = [('appendix_a_stakeholders', True), ('appendix_b_matrix', True), ('appendix_c_budget', True),
              ('appendix_d_calendar', True), ('appendix_e_methods', False), ('appendix_f_sources', True),
              ('appendix_g_launch', False)]
FIGURE_1 = ('reports/figures/fig1_waves.png',
            'Рис. 1. Поиск «Электрозавод» в Яндексе (Москва и область) и подписи под письмом «Архи.ру» по неделям, '
            'июнь–октябрь 2026 года')
FONT = 'Times New Roman'
INK_2 = RGBColor(0x52, 0x51, 0x4E)
SPACING = {'now': 1.15}  # line spacing: main text 1.15, appendices 1.0


def marked(name):
    text = (DRAFTS / f'{name}.md').read_text(encoding='utf-8')
    m = re.search(r'<!-- text -->\n(.*?)\n<!-- /text -->', text, re.S)
    if not m:
        raise SystemExit(f'{name}: no marked text')
    return m.group(1).strip()


def set_font(run, size=12, bold=False, italic=False, colour=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if colour:
        run.font.color.rgb = colour
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts')
        rpr.insert(0, fonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        fonts.set(qn(attr), FONT)


def para(doc, text='', size=12, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True,
         after=6, before=0, keep_next=False, colour=None):
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    fmt.alignment = align
    fmt.first_line_indent = Cm(1.0) if indent else None
    fmt.space_after, fmt.space_before = Pt(after), Pt(before)
    fmt.line_spacing = SPACING['now']
    fmt.keep_with_next = keep_next
    if text:
        set_font(p.add_run(text), size, bold, italic, colour)
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(level=level)
    fmt = p.paragraph_format
    fmt.space_before, fmt.space_after = Pt(10 if level == 1 else 6), Pt(6)
    fmt.keep_with_next = True
    set_font(p.add_run(text), 14 if level == 1 else 12, bold=True, colour=RGBColor(0, 0, 0))
    return p


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement('w:tblHeader')
    el.set(qn('w:val'), 'true')
    trpr.append(el)


def cell_margins(table, cm=0.1):
    tblpr = table._tbl.tblPr
    mar = OxmlElement('w:tblCellMar')
    for side in ('top', 'left', 'bottom', 'right'):
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:w'), str(int(cm * 567)))
        el.set(qn('w:type'), 'dxa')
        mar.append(el)
    tblpr.append(mar)


def add_table(doc, lines, width_cm, size):
    rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines if not re.match(r'^\|[-|\s]+\|$', l)]
    ncol = len(rows[0])
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    weights = []
    for j in range(ncol):
        body = [len(r[j]) for r in rows[1:]] or [0]
        word = max((len(w) for w in rows[0][j].split()), default=4)
        weights.append(max(word, sum(body) / len(body), 0.6 * min(max(body), 80), 4) ** 0.85)
    # every column is at least as wide as its longest unbreakable token (about 0.19 cm per character at 9 pt)
    tokens = [max(len(w) for r in rows for w in (r[j].split() or [''])) for j in range(ncol)]
    mins = [min(n, 16) * size * 0.021 + 0.3 for n in tokens]
    spare = max(width_cm - sum(mins), 0)
    widths = [m + spare * w / sum(weights) for m, w in zip(mins, weights)]
    table = doc.add_table(rows=len(rows), cols=ncol)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell_margins(table)
    layout = OxmlElement('w:tblLayout')
    layout.set(qn('w:type'), 'fixed')
    table._tbl.tblPr.append(layout)
    for j, col in enumerate(table.columns):
        col.width = Cm(widths[j])
    for i, r in enumerate(rows):
        for j, text in enumerate(r):
            c = table.cell(i, j)
            c.width = Cm(widths[j])
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            set_font(p.add_run(text), size, bold=(i == 0))
    repeat_header(table.rows[0])
    para(doc, after=4, indent=False)


def add_figure(doc, path, caption, width_cm, max_height_cm=14.0):
    with Image.open(ROOT / path) as im:
        aspect = im.width / im.height
    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=2, keep_next=True)
    p.add_run().add_picture(str(ROOT / path), width=Cm(min(width_cm, max_height_cm * aspect)))
    para(doc, caption, size=10, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=8,
         colour=INK_2)
    return len(caption)


def render(doc, text, width_cm, table_size, number=None):
    """Render one marked block; returns its character count as it appears in the document."""
    count = 0
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith('## '):
            title = line[3:].strip()
            if number:
                title = f'{number}. {title}'
            heading(doc, title)
            count += len(title)
        elif line.startswith('|'):
            block = []
            while i < len(lines) and lines[i].startswith('|'):
                block.append(lines[i])
                i += 1
            add_table(doc, block, width_cm, table_size)
            continue
        elif line.strip() == '[[pagebreak]]':
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        elif line.startswith('[[figure:'):
            path, caption, *height = line[len('[[figure:'):-2].split('|')
            count += add_figure(doc, path, caption, width_cm, float(height[0]) if height else 14.0)
        elif re.match(r'^\d+\. ', line):
            p = para(doc, line.strip(), indent=False, after=3)
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.first_line_indent = Cm(-0.6)
            count += len(line.strip())
        elif line.startswith('**') and line.endswith('**'):
            para(doc, line.strip('*'), bold=True, indent=False, keep_next=True, before=4)
            count += len(line.strip('*'))
        else:
            p = para(doc, line.strip())
            if line.rstrip().endswith(':'):
                p.paragraph_format.keep_with_next = True
            count += len(line.strip())
        i += 1
    return count


def page_number_footer(section):
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    set_font(run, 10)
    for kind, text in (('begin', None), (None, 'PAGE'), ('end', None)):
        if kind:
            el = OxmlElement('w:fldChar')
            el.set(qn('w:fldCharType'), kind)
        else:
            el = OxmlElement('w:instrText')
            el.set(qn('xml:space'), 'preserve')
            el.text = text
        run._r.append(el)


def set_page(section, landscape):
    w, h = Cm(21.0), Cm(29.7)
    section.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    section.page_width, section.page_height = (h, w) if landscape else (w, h)
    section.top_margin = section.bottom_margin = Cm(2.0)
    section.left_margin, section.right_margin = Cm(2.5), Cm(1.5)
    return (29.7 if landscape else 21.0) - 4.0


def title_page(doc):
    for _ in range(6):
        para(doc, indent=False)
    para(doc, 'Группа «Эталон»', size=14, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=36)
    para(doc, 'Электрозавод: коммуникационная стратегия редевелопмента', size=20, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=12)
    para(doc, 'Аналитический отчёт', size=14, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=6)
    para(doc, 'Кампания ноябрь 2026 – март 2027 года', size=14, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False,
         after=6)
    for _ in range(14):
        para(doc, indent=False)
    para(doc, 'Москва, октябрь 2026', size=12, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', default=str(ROOT / 'deliverables/Elektrozavod_report.docx'))
    parser.add_argument('--main-only', action='store_true', help='title page and main text only')
    args = parser.parse_args()

    doc = Document()
    normal = doc.styles['Normal']
    normal.font.name, normal.font.size = FONT, Pt(12)
    normal.element.get_or_add_rPr()
    width = set_page(doc.sections[0], False)
    doc.sections[0].different_first_page_header_footer = True
    page_number_footer(doc.sections[0])
    title_page(doc)
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)

    chars = 0
    for k, name in enumerate(MAIN):
        chars += render(doc, marked(name), width, 10, number=k if k else None)
        if name == 's1_situation':
            chars += add_figure(doc, *FIGURE_1, width_cm=width * 0.8, max_height_cm=8.0)

    if not args.main_only:
        SPACING['now'] = 1.0
        for name, landscape in APPENDICES:
            section = doc.add_section(WD_SECTION.NEW_PAGE)
            w = set_page(section, landscape)
            render(doc, marked(name), w, 9)

    out = Path(args.out)
    if args.main_only:
        out = out.with_name(out.stem + '_main.docx')
    doc.save(out)
    print(f'{out}: main text {chars:,} characters with spaces (limit 10,000)')


if __name__ == '__main__':
    main()
