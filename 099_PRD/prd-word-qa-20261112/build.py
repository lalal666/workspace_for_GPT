import re
import sys
from pathlib import Path
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Cm, Pt, RGBColor

source = Path(sys.argv[1]).read_text(encoding="utf-8")
output = Path(sys.argv[2])
if output.exists():
    raise FileExistsError(output)
doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Cm(21), Cm(29.7)
section.left_margin = section.right_margin = Cm(2)
section.top_margin, section.bottom_margin = Cm(1.9), Cm(1.85)
section.footer_distance = Cm(.85)
doc.core_properties.title = "低功耗电流检测器产品需求文档"
doc.core_properties.subject = "产品需求、接口与验收"
doc.core_properties.author = ""

def xml(parent, tag, **attributes):
    element = OxmlElement(tag)
    for key, value in attributes.items():
        element.set(qn("w:" + key), str(value))
    parent.append(element)
    return element

def para_style(name, size, before=0, after=0, line=1.15, bold=False, keep=False, color="000000"):
    style = doc.styles[name] if name in doc.styles else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.font.name = "Calibri"
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.italic = False
    style.font.color.rgb = RGBColor.from_string(color)
    rfonts = style.element.get_or_add_rPr().rFonts
    for key in list(rfonts.attrib):
        if key.lower().endswith("theme"):
            del rfonts.attrib[key]
    rfonts.set(qn("w:eastAsia"), "等线")
    rfonts.set(qn("w:cs"), "Calibri")
    fmt = style.paragraph_format
    fmt.space_before, fmt.space_after, fmt.line_spacing = Pt(before), Pt(after), line
    fmt.keep_with_next = fmt.keep_together = keep
    fmt.widow_control = True
    ppr = style.element.get_or_add_pPr()
    border = ppr.find(qn("w:pBdr"))
    if border is not None:
        ppr.remove(border)
    return style

para_style("Normal", 11, 3, 6, 1.18)
para_style("Title", 25, after=9, bold=True, keep=True)
para_style("Heading 1", 15.5, 12, 6, bold=True, keep=True)
para_style("Heading 2", 12, 10, 4, bold=True, keep=True)
para_style("PRD Status", 10.5, after=8, bold=True, keep=True)
para_style("PRD Note", 10.5, 3, 6, color="344054")
para_style("PRD Table Text", 10.5, line=1.13)
para_style("PRD Table Header", 10.5, line=1.13, bold=True)
para_style("PRD Page Number", 9, color="475467")
para_style("PRD Contents Heading", 13, 8, 5, bold=True, keep=True)
para_style("TOC 1", 10.5, after=1.5, line=1.05)
para_style("List Number", 11, 3, 6)

grid = doc.styles.add_style("PRD Matrix", WD_STYLE_TYPE.TABLE)
table_style = xml(grid.element, "w:tblPr")
borders = xml(table_style, "w:tblBorders")
for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
    xml(borders, "w:" + side, val="single", sz=5, color="D9D9D9")
padding = xml(table_style, "w:tblCellMar")
for side, value in (("top", 82), ("left", 110), ("bottom", 82), ("right", 110)):
    xml(padding, "w:" + side, w=value, type="dxa")

link_style = doc.styles.add_style("Hyperlink", WD_STYLE_TYPE.CHARACTER)
link_style.font.color.rgb = RGBColor.from_string("174A7A")
link_style.font.underline = True

def link(paragraph, label, target, anchor=False):
    if target.startswith("http://%"):
        paragraph.add_run(label)
        return
    item = OxmlElement("w:hyperlink")
    if anchor:
        item.set(qn("w:anchor"), target)
    else:
        item.set(qn("r:id"), paragraph.part.relate_to(target, RT.HYPERLINK, is_external=True))
    run = xml(item, "w:r")
    xml(xml(run, "w:rPr"), "w:rStyle", val="Hyperlink")
    xml(run, "w:t").text = label
    paragraph._p.append(item)

markup = re.compile(r'<mention url="([^"]+)">([^<]+)</mention>|<date start="([^"]+)"[^>]*/>|\[([^\]]+)\]\(([^)\s]+)\)|<b>([^<]+)</b>|\*\*([^*]+)\*\*|<code>([^<]+)</code>')

def inline(paragraph, content):
    pos = 0
    for match in markup.finditer(content):
        if match.start() > pos:
            paragraph.add_run(content[pos:match.start()])
        url, label, date, link_text, target, bold, strong, literal = match.groups()
        if url:
            link(paragraph, label, url)
        elif date:
            paragraph.add_run(date)
        elif link_text:
            link(paragraph, link_text, target)
        else:
            run = paragraph.add_run(bold or strong or literal)
            run.bold = bool(bold or strong)
        pos = match.end()
    if pos < len(content):
        paragraph.add_run(content[pos:])

def field_begin(p, instruction):
    xml(p.add_run()._r, "w:fldChar", fldCharType="begin")
    code = xml(p.add_run()._r, "w:instrText")
    code.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    code.text = instruction
    xml(p.add_run()._r, "w:fldChar", fldCharType="separate")

def field_end(p):
    xml(p.add_run()._r, "w:fldChar", fldCharType="end")

widths = {
    "0": (3.1, 6.75, 7.15), "1": (3.6, 5.8, 7.6), "2": (3.1, 6.7, 7.2),
    "3": (3, 5.25, 8.75), "4": (2.25, 2.9, 8.7, 3.15), "5": (3.1, 6.1, 7.8),
    "6": (2.2, 4.5, 5.4, 4.9), "7": (3.1, 5, 8.9), "9": (1.6, 3.45, 9.25, 2.7),
    "10": (1.8, 6.25, 3.4, 5.55), "A": (1.75, 2.95, 5.85, 6.45),
}
centers = {"4": {0, 1, 3}, "6": {0}, "9": {0, 1, 3}, "10": {0}, "A": {0}}

def split_row(line):
    return [text.strip().replace(r"\|", "|") for text in re.split(r"(?<!\\)\|", line[1:-1])]

def add_table(rows, key):
    dims = widths[key]
    data = [r for r in rows if not all(re.fullmatch(r":?-{3,}:?", c) for c in r)]
    assert all(len(row) == len(dims) for row in data), (key, data[0])
    table = doc.add_table(rows=len(data), cols=len(dims))
    table.style = "PRD Matrix"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, column in enumerate(table.columns):
        column.width = Cm(dims[i])
    for i, row in enumerate(table.rows):
        props = row._tr.get_or_add_trPr()
        xml(props, "w:cantSplit")
        if i == 0:
            xml(props, "w:tblHeader", val=1)
        for j, cell in enumerate(row.cells):
            cell.width = Cm(dims[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if i == 0:
                xml(cell._tc.get_or_add_tcPr(), "w:shd", val="clear", color="auto", fill="E7EFF8")
            p = cell.paragraphs[0]
            p.style = "PRD Table Header" if i == 0 else "PRD Table Text"
            if i == 0:
                p.paragraph_format.keep_with_next = True
            if j in centers.get(key, set()):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            inline(p, data[i][j])

def clean_heading(text):
    return text.replace("　", " ").replace("、", " ")

headings = [clean_heading(line[3:]) for line in source.splitlines() if line.startswith("## ")]
doc.add_paragraph("低功耗电流检测器产品需求文档", "Title")
doc.add_paragraph("PRD 送审准备稿", "PRD Status")
key = ""
rows = []
heading_index = 0
for line in [*source.splitlines(), ""]:
    line = line.strip()
    if line.startswith("|") and line.endswith("|"):
        rows.append(split_row(line))
        continue
    if rows:
        add_table(rows, key)
        rows.clear()
    if not line:
        continue
    if line.startswith("> "):
        inline(doc.add_paragraph(style="PRD Note"), line[2:])
    elif line.startswith("<table-of-contents"):
        doc.add_paragraph("目录", "PRD Contents Heading")
        for index, heading in enumerate(headings, 1):
            p = doc.add_paragraph(style="TOC 1")
            if index == 1:
                field_begin(p, ' TOC \\o "1-1" \\h \\z ')
            link(p, heading, f"PRDChapter{index}", anchor=True)
            if index == len(headings):
                field_end(p)
    elif line.startswith("### "):
        doc.add_paragraph(clean_heading(line[4:]), "Heading 2")
    elif line.startswith("## "):
        heading_index += 1
        heading = clean_heading(line[3:])
        key = heading.split(".")[0] if heading[0].isdigit() else "A"
        p = doc.add_paragraph(style="Heading 1")
        xml(p._p, "w:bookmarkStart", id=heading_index, name=f"PRDChapter{heading_index}")
        p.add_run(heading)
        xml(p._p, "w:bookmarkEnd", id=heading_index)
    elif re.match(r"^\d+\. ", line):
        inline(doc.add_paragraph(style="List Number"), re.sub(r"^\d+\. ", "", line))
    else:
        inline(doc.add_paragraph(), line)

footer = section.footer.paragraphs[0]
footer.style = "PRD Page Number"
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
field_begin(footer, " PAGE ")
footer.add_run("1")
field_end(footer)
doc.save(output)
print(output)
print(f"tables={len(doc.tables)} heading1={heading_index}")
