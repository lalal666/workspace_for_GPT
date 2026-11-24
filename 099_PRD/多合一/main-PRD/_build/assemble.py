# -*- coding: utf-8 -*-
"""把各 SKU 的骨架稿与 SKU2 V4.3 的公共章节装配成最终 PRD。

用法：
    python _build/assemble.py sku1
    python _build/assemble.py all

骨架稿（_build/src/*.md）中用 {{C:key}} 占位，装配时替换为 SKU2 V4.3 对应章节的原文。
公共章节因此逐字一致（只做 SKU 名称令牌替换），私有章节由骨架稿提供。
"""
import re
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "SKU2-双鉴存在传感器-PRD_V4.3.md")
SRC_DIR = os.path.join(BASE, "_build", "src")
OUT_DIR = os.path.abspath(os.path.join(BASE, "..", "main"))

TARGETS = {
    "sku1": {
        "src": "sku1.md",
        "out": "SKU1-PIR人体移动传感器-PRD_V3.0.md",
        "name": "SKU1 红外移动传感器",
    },
    "sku3": {
        "src": "sku3.md",
        "out": "SKU3-温照度传感器-PRD_V2.0.md",
        "name": "SKU3 温照度传感器",
    },
    "sku4": {
        "src": "sku4.md",
        "out": "SKU4-温感红外空调控制器-PRD_V2.0.md",
        "name": "SKU4 温感红外空调控制器",
    },
}


def load_lines():
    with open(SRC, encoding="utf-8") as f:
        return f.read().split("\n")


def find_sections(lines):
    """返回 key -> (start, end)，end 为下一个同级或更高级标题的行号。"""
    heads = []
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(\d+(?:\.\d+)*)[\s\u3000]", ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    out = {}
    for idx, (i, lvl, key) in enumerate(heads):
        end = len(lines)
        for j, lvl2, _ in heads[idx + 1:]:
            if lvl2 <= lvl:
                end = j
                break
        out[key] = (i, end)
    return out


def trim_end(text):
    return text.rstrip("\n")


def build_section(lines, secs, key, name):
    if key not in secs:
        raise KeyError("公共章节不存在: %s" % key)
    s, e = secs[key]
    body = "\n".join(lines[s:e])
    body = trim_end(body)
    # 只做产品名替换，其余逐字保留
    body = body.replace("SKU2 双鉴存在传感器", name)
    body = re.sub(r"SKU2 →", name + " →", body)
    body = body.replace("小程序 ↔ SKU2", "小程序 ↔ " + name)
    return body


def build_partial(lines, secs, key, start_pat=None, end_pat=None, name=""):
    if key not in secs:
        raise KeyError("公共章节不存在: %s" % key)
    s, e = secs[key]
    sub = lines[s:e]
    if start_pat is not None:
        for i, ln in enumerate(sub):
            if re.search(start_pat, ln):
                sub = sub[i:]
                break
        else:
            raise KeyError("找不到起始标记 %s in %s" % (start_pat, key))
    if end_pat is not None:
        for i, ln in enumerate(sub):
            if re.search(end_pat, ln):
                sub = sub[:i]
                break
        else:
            raise KeyError("找不到结束标记 %s in %s" % (end_pat, key))
    body = "\n".join(sub).rstrip("\n")
    body = body.replace("SKU2 双鉴存在传感器", name)
    body = re.sub(r"SKU2 →", name + " →", body)
    body = body.replace("小程序 ↔ SKU2", "小程序 ↔ " + name)
    return body


def assemble(tkey):
    cfg = TARGETS[tkey]
    lines = load_lines()
    secs = find_sections(lines)
    name = cfg["name"]
    src_path = os.path.join(SRC_DIR, cfg["src"])
    with open(src_path, encoding="utf-8") as f:
        tpl = f.read()

    def repl(m):
        key = m.group(1)
        if key == "4.8a":
            return build_partial(lines, secs, "4.8", end_pat=r"^\| FR-805 \|", name=name)
        if key == "4.8b":
            return build_partial(lines, secs, "4.8", start_pat=r"^\| FR-807 \|", name=name)
        return build_section(lines, secs, key, name)

    out = re.sub(r"\{\{C:([0-9.]+|4\.8[ab])\}\}", repl, tpl)
    left = re.findall(r"\{\{C:[^}]+\}\}", out)
    if left:
        raise SystemExit("未替换的占位符: %s" % left)

    # 占位符本身带标题，模板里若已写了同名标题会产生重复；这里去掉紧邻的重复标题
    dedup = []
    for ln in out.split("\n"):
        if ln.startswith("#") and dedup:
            j = len(dedup) - 1
            while j >= 0 and dedup[j].strip() == "":
                j -= 1
            if j >= 0 and dedup[j] == ln:
                while dedup and dedup[-1].strip() == "":
                    dedup.pop()
                continue
        dedup.append(ln)
    out = "\n".join(dedup)

    # 统一修正 SKU2 遗留的防拆编号笔误（FR-120/FR-121 -> FR-1210/FR-1211）
    out = out.replace("| FR-120  |", "| FR-1210 |").replace("| FR-121  |", "| FR-1211 |")
    out = out.replace("FR-120/FR-121", "FR-1210/FR-1211")

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    dst = os.path.join(OUT_DIR, cfg["out"])
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(out.rstrip("\n") + "\n")
    print("OK -> %s (%d 行)" % (dst, out.count("\n") + 1))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    keys = TARGETS.keys() if arg == "all" else [arg]
    for k in keys:
        assemble(k)
