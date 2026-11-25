# -*- coding: utf-8 -*-
"""校验装配结果：公共章节是否与 SKU2 V4.3 逐字一致（仅允许产品名替换）。"""
import re
import os
import sys
import difflib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "SKU2-双鉴存在传感器-PRD_V4.3.md")
OUT_DIR = os.path.abspath(os.path.join(BASE, "..", "main"))

COMMON = ["1.4.2", "3.1.1", "3.1.3", "4.1.1", "4.2", "4.3", "4.4.1", "4.4.3", "4.4.4",
          "4.5", "4.6", "4.7", "5.1", "5.4", "5.7"]

FILES = {
    "sku1": ("SKU1-PIR人体移动传感器-PRD_V3.0.md", "SKU1 红外移动传感器"),
    "sku2": ("SKU2-双鉴存在传感器-PRD_V4.4.md", "SKU2 双鉴存在传感器"),
    "sku3": ("SKU3-温照度传感器-PRD_V2.0.md", "SKU3 温照度传感器"),
    "sku4": ("SKU4-温感红外空调控制器-PRD_V2.0.md", "SKU4 温感红外空调控制器"),
}


def sections(path):
    lines = open(path, encoding="utf-8").read().split("\n")
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
        out[key] = "\n".join(lines[i:end]).rstrip("\n")
    return out


def norm(t, name):
    t = t.replace("SKU2 双鉴存在传感器", name)
    t = t.replace("SKU2 →", name + " →")
    t = t.replace("小程序 ↔ SKU2", "小程序 ↔ " + name)
    t = t.replace("| FR-120  |", "| FR-1210 |").replace("| FR-121  |", "| FR-1211 |")
    return t


def main():
    src = sections(SRC)
    rc = 0
    tamper = {}
    for k, (fn, name) in FILES.items():
        p = os.path.join(OUT_DIR, fn)
        if not os.path.exists(p):
            print("[SKIP] %s 不存在" % fn)
            continue
        out = sections(p)
        tamper[fn] = out.get("4.12", "")
        print("=" * 20, fn)
        for key in COMMON:
            a = norm(src.get(key, ""), name)
            b = out.get(key, "")
            if not b:
                print("  [MISS] %s" % key)
                rc = 1
                continue
            if a == b:
                print("  [SAME] %-6s %d 行" % (key, a.count("\n") + 1))
            else:
                print("  [DIFF] %-6s" % key)
                for ln in list(difflib.unified_diff(a.split("\n"), b.split("\n"), lineterm="", n=1))[:24]:
                    print("        " + ln)
                rc = 1
    vals = [v for v in tamper.values() if v]
    if len(vals) >= 2:
        base = vals[0]
        print("=" * 20, "4.12 修正版跨 SKU 一致性")
        for fn, v in tamper.items():
            if v == base:
                print("  [SAME] %s" % fn)
            else:
                print("  [DIFF] %s" % fn)
                rc = 1
    sys.exit(rc)


if __name__ == "__main__":
    main()
