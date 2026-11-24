# -*- coding: utf-8 -*-
"""PRD 结构自检：表格列数、mermaid 块、标题序列、编号唯一性与事件引用闭环。"""
import re
import os
import sys
import glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(os.path.join(BASE, "..", "main"))
FILES = sorted(glob.glob(os.path.join(OUT, "SKU*-PRD_V*.md")))

DIAG = ("flowchart", "graph", "stateDiagram", "sequenceDiagram", "erDiagram", "gantt", "classDiagram", "journey", "mindmap")


def check(path):
    txt = open(path, encoding="utf-8").read()
    lines = txt.split("\n")
    errs = []
    warns = []

    # 1) 占位符
    for m in re.findall(r"\{\{[^}]+\}\}", txt):
        errs.append("未替换占位符 %s" % m)

    # 2) mermaid
    fences = [i for i, l in enumerate(lines) if l.strip() == "```mermaid"]
    closes = [i for i, l in enumerate(lines) if l.strip() == "```"]
    if len(fences) * 2 > len(closes) + 0:
        pass
    for i in fences:
        # 找下一个 ```
        j = next((k for k in closes if k > i), None)
        if j is None:
            errs.append("mermaid 块未闭合 @%d" % (i + 1))
            continue
        body = [l for l in lines[i + 1:j] if l.strip()]
        if not body or not body[0].strip().startswith(DIAG):
            errs.append("mermaid 缺少合法图类型 @%d: %s" % (i + 1, body[0] if body else ""))
        if "subgraph" in body:
            n_sub = sum(1 for l in body if l.strip().startswith("subgraph"))
            n_end = sum(1 for l in body if l.strip() == "end")
            if n_sub != n_end:
                errs.append("mermaid subgraph/end 不配对 @%d (%d/%d)" % (i + 1, n_sub, n_end))

    # 3) 表格列数
    in_mermaid = False
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.strip() == "```mermaid":
            in_mermaid = True
        elif in_mermaid and l.strip() == "```":
            in_mermaid = False
        if not in_mermaid and l.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*[-: ]+\|", lines[i + 1]):
            header_cols = l.count("|")
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                if lines[j].count("|") != header_cols:
                    errs.append("表格列数不一致 @%d: 期望 %d 实际 %d | %s" % (j + 1, header_cols, lines[j].count("|"), lines[j][:60]))
                j += 1
            i = j
            continue
        i += 1

    # 4) 标题编号
    heads = []
    for idx, l in enumerate(lines):
        m = re.match(r"^(##|###|####)\s+(\d+(?:\.\d+)*)[\s\u3000]", l)
        if m:
            heads.append((idx + 1, len(m.group(1)), m.group(2)))
    for k in range(1, len(heads)):
        prev, cur = heads[k - 1], heads[k]
        if cur[1] > prev[1]:
            continue
        if cur[1] == prev[1] == 2:
            a = int(prev[2]); b = int(cur[2])
            if b != a + 1:
                warns.append("章号不连续: %s -> %s" % (prev[2], cur[2]))

    # 5) 编号唯一（FR/NFR）
    for pref in ("FR", "NFR"):
        ids = re.findall(r"\| (%s-\d+)\s*\|" % pref, txt)
        dup = {x for x in ids if ids.count(x) > 1}
        if dup:
            errs.append("%s 编号重复: %s" % (pref, sorted(dup)))
    # 6) 事件引用闭环
    defined = set(re.findall(r"\| (E\d{3}) \|", txt))
    refs = set(re.findall(r"\b(E\d{3})\b", txt))
    missing = sorted(refs - defined)
    if missing:
        errs.append("引用了未定义事件: %s" % missing)

    # 7) 型号唯一性
    models = set(re.findall(r"LC-[A-Z0-9-]{8,}", txt))
    if len(models) > 1:
        warns.append("出现多个型号: %s" % sorted(models))

    return errs, warns, len(fences)


def main():
    rc = 0
    for p in FILES:
        errs, warns, nfig = check(p)
        print("=" * 24, os.path.basename(p), "| 图:", nfig)
        for w in warns:
            print("  [WARN]", w)
        for e in errs:
            print("  [FAIL]", e)
            rc = 1
        if not errs:
            print("  [PASS] 结构自检通过")
    sys.exit(rc)


if __name__ == "__main__":
    main()
