# -*- coding: utf-8 -*-
"""SKU2 PRD Markdown -> 单文件 HTML（侧栏导航 + 章节折叠 + mermaid 矢量渲染）
仅依赖标准库；mermaid.min.js 内嵌，离线可用。
"""
import re, html, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
MD = os.path.join(ROOT, 'SKU2-双鉴存在传感器-PRD_V3.0.md')
OUT = os.path.join(ROOT, 'SKU2-双鉴存在传感器-PRD_V3.0.html')
MERMAID = os.path.join(BASE, 'mermaid.min.js')

# ---------- 工具 ----------
_used_ids = set()

def slug(text):
    t = text.strip().lower()
    t = re.sub(r'[^\w\u4e00-\u9fff.\- ]', '', t)
    t = t.replace(' ', '-')
    t = re.sub(r'-{2,}', '-', t).strip('-')
    if not t:
        t = 'sec'
    base, i = t, 2
    while t in _used_ids:
        t = '%s-%d' % (base, i); i += 1
    _used_ids.add(t)
    return t

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
               lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), s)
    return s

ID_RE = re.compile(r'^(?:FR|NFR)-\d+$|^E\d{3}$|^D-\d{2}$|^R-\d{2}$|^TC-\d{2,3}$')
PILL_RE = re.compile(r'^P[0-3]$')

def cell(s, header=False):
    txt = inline(s.strip())
    if not header:
        plain = re.sub(r'<[^>]+>', '', txt).strip()
        if PILL_RE.match(plain):
            return '<span class="pill p%s">%s</span>' % (plain[1], plain)
        if ID_RE.match(plain):
            return '<span class="idc">%s</span>' % plain
        if re.fullmatch(r'[A-Z][A-Z0-9]*(?:-[A-Z0-9]+){2,}', plain) or re.fullmatch(r'[0-9A-F]{2}(?: [0-9A-FX]{2}){5}', plain):
            return '<span class="partno">%s</span>' % txt
        m = re.match(r'^(\d{1,2})\s*(高|中高|中|低)$', plain)
        if m:
            lv = {'高': 'hi', '中高': 'midhi', '中': 'mid', '低': 'lo'}[m.group(2)]
            return '<span class="lv lv-%s">%s %s</span>' % (lv, m.group(1), m.group(2))
    return txt

# ---------- 解析 ----------
raw = open(MD, encoding='utf-8').read().replace('\r\n', '\n')
lines = raw.split('\n')

blocks = []        # 内容块
nav = []           # 导航条目
cur_head = ''      # 最近标题（用于图注）

i, n = 0, len(lines)
while i < n:
    line = lines[i]
    s = line.strip()

    if not s:
        i += 1; continue

    # 代码块
    if s.startswith('```'):
        lang = s[3:].strip().lower()
        buf = []
        i += 1
        while i < n and not lines[i].strip().startswith('```'):
            buf.append(lines[i]); i += 1
        i += 1
        code = '\n'.join(buf)
        if lang == 'mermaid':
            blocks.append({'t': 'mermaid', 'code': code, 'cap': cur_head})
        else:
            blocks.append({'t': 'code', 'code': code, 'lang': lang})
        continue

    # 标题
    m = re.match(r'^(#{1,6})\s+(.*)$', line)
    if m:
        lvl = len(m.group(1)); text = m.group(2).strip()
        num, title = '', text
        mn = re.match(r'^(\d+(?:\.\d+)*)[\.\s]+(.*)$', text)
        if mn and lvl >= 2:
            num, title = mn.group(1), mn.group(2)
        hid = slug(text) if lvl > 1 else slug(title)
        blocks.append({'t': 'h', 'lvl': lvl, 'id': hid, 'num': num, 'title': title, 'raw': text})
        if 2 <= lvl <= 4:
            nav.append({'lvl': lvl, 'id': hid, 'num': num, 'title': title, 'text': (num + ' ' + title).strip()})
        if lvl >= 2:
            cur_head = (num + ' ' + title).strip()
        else:
            cur_head = title
        i += 1; continue

    # 表格
    if s.startswith('|'):
        rows = []
        while i < n and lines[i].strip().startswith('|'):
            rows.append(lines[i].strip()); i += 1
        if len(rows) >= 2 and re.match(r'^\|[\s:\-\|]+\|?$', rows[1]):
            blocks.append({'t': 'table', 'rows': rows})
            continue
        # 不是标准表格，退化为段落
        blocks.append({'t': 'p', 'text': ' '.join(r.strip('|') for r in rows)})
        continue

    # 引用
    if s.startswith('>'):
        buf = []
        while i < n and lines[i].strip().startswith('>'):
            buf.append(lines[i].strip().lstrip('>').strip()); i += 1
        blocks.append({'t': 'quote', 'text': ' '.join(x for x in buf if x)})
        continue

    # 列表
    if re.match(r'^[-*]\s+', s) or re.match(r'^\d+\.\s+', s):
        ordered = bool(re.match(r'^\d+\.\s+', s))
        pat = r'^\d+\.\s+' if ordered else r'^[-*]\s+'
        items = []
        while i < n:
            t = lines[i].strip()
            if re.match(pat, t):
                items.append(re.sub(pat, '', t)); i += 1
            else:
                break
        blocks.append({'t': 'ol' if ordered else 'ul', 'items': items})
        continue

    # 段落（连续非空行合并）
    buf = []
    while i < n and lines[i].strip() and not lines[i].strip().startswith(('|', '#', '```', '>')):
        buf.append(lines[i].strip()); i += 1
    blocks.append({'t': 'p', 'text': ' '.join(buf)})

# ---------- 组装正文 ----------
out = []
stack = []
open_tags = {2: '<section class="chapter" id="%s"><div class="chapter-body">',
             3: '<section class="sec" id="%s"><div class="sec-body">',
             4: '<section class="sub" id="%s"><div class="sub-body">'}

def close_to(level):
    while stack and stack[-1][0] >= level:
        lv, _ = stack.pop()
        out.append('</div></section>')

diag_no = 0
for b in blocks:
    if b['t'] == 'h':
        lvl = b['lvl']
        if lvl == 1:
            close_to(2)
            out.append('<h1 class="hero-title">%s</h1>' % inline(b['title']))
            continue
        if lvl > 4:
            out.append('<h5>%s</h5>' % inline(b['raw']))
            continue
        close_to(lvl)
        anchor = ' id="%s"' % b['id'] if lvl == 2 else ''
        cls = {2: 'h2', 3: 'h3', 4: 'h4'}[lvl]
        num = '<span class="hnum">%s</span>' % b['num'] if b['num'] else ''
        tog = '<button class="tg" type="button" aria-label="折叠本章节"></button>' if lvl in (2, 3) else ''
        h = '<h%d class="%s"%s>%s%s<span class="htxt">%s</span></h%d>' % (
            lvl, cls, anchor, tog, num, inline(b['title']), lvl)
        # id 放在 section 上（h2 直接在 section 上），h3/h4 的 section 需要 id
        if lvl == 2:
            out.append('<section class="chapter" id="%s">' % b['id'])
            out.append(h.replace(' id="%s"' % b['id'], ''))
            out.append('<div class="chapter-body">')
        else:
            out.append('<section class="%s" id="%s">' % ({3: 'sec', 4: 'sub'}[lvl], b['id']))
            out.append(h)
            out.append('<div class="%s-body">' % {3: 'sec', 4: 'sub'}[lvl])
        stack.append((lvl, b['id']))
        continue

    if b['t'] == 'p':
        t = inline(b['text'])
        if t.startswith('<strong>要点</strong>'):
            out.append('<div class="keypoint">%s</div>' % t)
        elif b['text'].strip().strip('*').strip() == '目录':
            out.append('<p class="toc-label">目录</p>')
        else:
            out.append('<p>%s</p>' % t)
        continue

    if b['t'] == 'ul':
        out.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % inline(x) for x in b['items']))
        continue

    if b['t'] == 'ol':
        is_toc = (len(b['items']) >= 5 and
                  all(re.match(r'^\[[^\]]+\]\(#[^)]+\)$', x.strip()) for x in b['items']))
        cls = ' class="toc-inline"' if is_toc else ''
        out.append('<ol%s>%s</ol>' % (cls, ''.join('<li>%s</li>' % inline(x) for x in b['items'])))
        continue

    if b['t'] == 'quote':
        t = inline(b['text'])
        warn = any(k in b['text'] for k in ('风险', '不得', '红线', '禁止'))
        out.append('<div class="callout%s">%s</div>' % (' warn' if warn else '', t))
        continue

    if b['t'] == 'code':
        out.append('<pre class="code"><code>%s</code></pre>' % html.escape(b['code']))
        continue

    if b['t'] == 'table':
        rows = b['rows']
        head = [c for c in rows[0].strip().strip('|').split('|')]
        body = rows[2:]
        wide = ' wide' if len(head) >= 6 else ''
        th = ''.join('<th>%s</th>' % cell(c, True) for c in head)
        trs = []
        for r in body:
            cs = r.strip().strip('|').split('|')
            if len(cs) < len(head):
                cs += [''] * (len(head) - len(cs))
            trs.append('<tr>%s</tr>' % ''.join('<td>%s</td>' % cell(c) for c in cs[:len(head)]))
        out.append('<div class="tw"><table class="tbl%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
                   % (wide, th, ''.join(trs)))
        continue

    if b['t'] == 'mermaid':
        diag_no += 1
        cap = b['cap'] or '结构示意'
        out.append(
            '<figure class="diagram"><div class="dg-tools">'
            '<button class="dg-btn" type="button">放大</button></div>'
            '<pre class="mermaid">%s</pre>'
            '<figcaption><b>图 %d</b> · %s</figcaption></figure>'
            % (html.escape(b['code']), diag_no, html.escape(cap)))
        continue

close_to(0)
article = '\n'.join(out)

# ---------- 组装导航 ----------
tree, st = [], []
for e in nav:
    node = {'lvl': e['lvl'], 'id': e['id'], 'num': e['num'], 'title': e['title'], 'text': e['text'], 'kids': []}
    while st and st[-1]['lvl'] >= e['lvl']:
        st.pop()
    (st[-1]['kids'] if st else tree).append(node)
    st.append(node)

def render_nav(nodes, depth=1):
    parts = []
    for nd in nodes:
        has = bool(nd['kids'])
        # 默认：章展开，节内小节收起
        collapsed = ' collapsed' if (depth >= 2 and has) else ''
        parts.append('<div class="ni lv%d%s">' % (depth, collapsed))
        parts.append('<div class="nr">')
        parts.append('<button class="caret" type="button" aria-label="展开/收起"></button>' if has
                     else '<span class="caret ghost"></span>')
        num = '<em>%s</em>' % html.escape(nd['num']) if nd['num'] else ''
        parts.append('<a class="nl" href="#%s" title="%s">%s<span>%s</span></a>'
                     % (nd['id'], html.escape(nd['text']), num, html.escape(nd['title'])))
        parts.append('</div>')
        if has:
            parts.append('<div class="nk">%s</div>' % render_nav(nd['kids'], depth + 1))
        parts.append('</div>')
    return ''.join(parts)

nav_html = render_nav(tree)
n_ch = sum(1 for e in nav if e['lvl'] == 2)
n_sec = sum(1 for e in nav if e['lvl'] == 3)

mermaid_js = open(MERMAID, encoding='utf-8').read().replace('</script', '<\\/script')

TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{
  --ink:#16202b; --ink2:#33414f; --muted:#6b7a88; --faint:#93a1ad;
  --line:#e3e8ee; --line2:#edf1f5; --bg:#f4f6f8; --card:#fff;
  --accent:#0f6b7a; --accent2:#12889b; --soft:#e9f4f6; --soft2:#f2f8f9;
  --amber:#9a5b0b; --amberbg:#fdf4e5; --red:#b42318; --redbg:#fdeceb;
  --sbw:308px; --top:56px;
  --mono:"JetBrains Mono","Cascadia Code",Consolas,"SFMono-Regular",Menlo,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Source Han Sans SC","Noto Sans CJK SC","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
     font-size:15px;line-height:1.8;-webkit-font-smoothing:antialiased}

/* ---------- 顶栏 ---------- */
.topbar{position:fixed;inset:0 0 auto 0;height:var(--top);z-index:60;display:flex;align-items:center;overflow:hidden;
  gap:16px;padding:0 18px 0 16px;background:rgba(255,255,255,.92);backdrop-filter:saturate(1.4) blur(8px);
  border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:10px;min-width:0}
.logo{width:26px;height:26px;border-radius:7px;flex:0 0 auto;
  background:linear-gradient(140deg,#12889b,#0b4f5c);position:relative;box-shadow:0 2px 6px rgba(15,107,122,.25)}
.logo:after{content:"";position:absolute;inset:7px;border:2px solid rgba(255,255,255,.9);border-radius:50% 50% 50% 0}
.bt{font-weight:650;font-size:14.5px;letter-spacing:.2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bsub{font-size:11.5px;color:var(--faint);letter-spacing:.4px;margin-top:-3px}
.chips{display:flex;gap:6px;margin-left:auto;flex-wrap:nowrap;overflow:hidden}
.chip{font-size:11.5px;padding:2px 9px;border-radius:20px;border:1px solid var(--line);
  color:var(--ink2);background:#fff;white-space:nowrap}
.chip.on{background:var(--soft);border-color:#c9e3e8;color:var(--accent)}
.tools{display:flex;gap:6px;margin-left:8px}
.tool{font:inherit;font-size:12.5px;border:1px solid var(--line);background:#fff;color:var(--ink2);
  padding:5px 11px;border-radius:7px;cursor:pointer;transition:.15s;white-space:nowrap}
.tool:hover{border-color:#c9d6e2;background:#f8fafc;color:var(--accent)}
.prog{position:absolute;left:0;bottom:-1px;height:2px;width:0;background:linear-gradient(90deg,#12889b,#0b4f5c);
  transition:width .1s linear}

/* ---------- 侧栏 ---------- */
.sidebar{position:fixed;left:0;top:var(--top);bottom:0;width:var(--sbw);z-index:50;display:flex;flex-direction:column;
  background:#fbfcfd;border-right:1px solid var(--line)}
.sb-head{padding:14px 16px 10px;border-bottom:1px solid var(--line2)}
.sb-title{font-size:12px;font-weight:700;letter-spacing:2px;color:var(--muted)}
.sb-stats{font-size:11px;color:var(--faint);margin-top:3px;letter-spacing:.3px}
.sb-search{margin-top:10px;position:relative}
.sb-search input{width:100%;font:inherit;font-size:12.5px;padding:7px 30px 7px 30px;border:1px solid var(--line);
  border-radius:8px;background:#fff;outline:none;transition:.15s;color:var(--ink)}
.sb-search input:focus{border-color:var(--accent2);box-shadow:0 0 0 3px rgba(18,136,155,.10)}
.sb-search .ico{position:absolute;left:9px;top:50%;transform:translateY(-50%);width:13px;height:13px;
  border:1.6px solid var(--faint);border-radius:50%}
.sb-search .ico:after{content:"";position:absolute;right:-4px;bottom:-3px;width:6px;height:1.6px;background:var(--faint);
  transform:rotate(45deg);border-radius:2px}
input[type=search]::-webkit-search-cancel-button{display:none}
.sb-search .clr{position:absolute;right:6px;top:50%;transform:translateY(-50%);border:0;background:none;cursor:pointer;
  color:var(--faint);font-size:14px;padding:2px 4px;display:none}
.sb-acts{display:flex;gap:6px;margin-top:8px}
.sb-acts button{flex:1;font:inherit;font-size:11.5px;padding:5px 0;border:1px solid var(--line);background:#fff;
  border-radius:6px;color:var(--muted);cursor:pointer}
.sb-acts button:hover{color:var(--accent);border-color:#cfe0e6}
.toc{flex:1;overflow:auto;padding:8px 8px 40px;scrollbar-width:thin}
.toc::-webkit-scrollbar{width:8px}
.toc::-webkit-scrollbar-thumb{background:#d8e0e7;border-radius:8px;border:2px solid #fbfcfd}
.ni{margin:1px 0}
.nr{display:flex;align-items:center;gap:1px;border-radius:7px;transition:.12s}
.nr:hover{background:#eef4f7}
.caret{flex:0 0 auto;width:18px;height:22px;border:0;background:none;cursor:pointer;position:relative;padding:0}
.caret:before{content:"";position:absolute;left:6px;top:8px;width:5px;height:5px;border-right:1.5px solid #8a99a6;
  border-bottom:1.5px solid #8a99a6;transform:rotate(45deg);transition:.15s}
.ni.collapsed>.nr .caret:before{transform:rotate(-45deg)}
.caret.ghost:before{display:none}
.nl{display:flex;gap:7px;align-items:baseline;text-decoration:none;color:var(--ink2);font-size:12.8px;
  padding:4px 6px 4px 2px;flex:1;min-width:0;line-height:1.5}
.nl span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.nl em{font-style:normal;font-family:var(--mono);font-size:11px;color:var(--faint);flex:0 0 auto;min-width:26px}
.ni.lv1>.nr .nl{font-weight:650;color:var(--ink);font-size:13.2px;padding-top:6px;padding-bottom:5px}
.ni.lv1{margin-top:4px;border-top:1px solid var(--line2);padding-top:2px}
.ni.lv1:first-child{border-top:0}
.ni.lv2 .nl{padding-left:14px}
.ni.lv3 .nl{padding-left:30px;font-size:12.2px;color:var(--muted)}
.nk{overflow:hidden}
.ni.collapsed>.nk{display:none}
.nl.active{color:var(--accent);font-weight:650;background:var(--soft);border-radius:6px}
.nl.hide,.ni.hide{display:none}

/* ---------- 正文 ---------- */
.main{margin-left:var(--sbw);padding-top:var(--top)}
.wrap{max-width:1060px;margin:0 auto;padding:30px 36px 120px}
article{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:44px 46px 56px;box-shadow:0 1px 2px rgba(16,32,48,.04),0 12px 32px -18px rgba(16,32,48,.18)}
.hero-title{font-size:31px;line-height:1.35;margin:0 0 10px;letter-spacing:-.4px;font-weight:700}
.hero-title:after{content:"";display:block;width:56px;height:3px;border-radius:2px;margin-top:14px;
  background:linear-gradient(90deg,var(--accent2),rgba(18,136,155,.15))}

p{margin:12px 0;color:var(--ink2)}
strong{color:var(--ink);font-weight:650}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(15,107,122,.25)}
a:hover{border-bottom-color:var(--accent)}
code{font-family:var(--mono);font-size:12.4px;background:#eef2f6;color:#25404f;padding:1.5px 5px;
  border-radius:4px;border:1px solid #e3eaf0}
ul,ol{margin:10px 0;padding-left:22px;color:var(--ink2)}
li{margin:5px 0}
li::marker{color:var(--accent2)}

/* 标题 + 折叠 */
h2,h3,h4,h5{position:relative;scroll-margin-top:78px}
.h2{font-size:24px;font-weight:700;letter-spacing:-.2px;margin:44px 0 6px;padding:26px 0 12px;
  border-top:1px solid var(--line);display:flex;align-items:center;gap:10px;cursor:default}
.chapter:first-of-type .h2{border-top:0;padding-top:6px;margin-top:12px}
.h2 .hnum{font-family:var(--mono);font-size:15px;color:#fff;background:linear-gradient(140deg,#12889b,#0b4f5c);
  padding:3px 9px;border-radius:7px;letter-spacing:.5px;box-shadow:0 2px 6px rgba(15,107,122,.2)}
.h3{font-size:17.5px;font-weight:650;margin:32px 0 4px;padding-left:12px;display:flex;align-items:center;gap:8px}
.h3:before{content:"";position:absolute;left:0;top:.42em;bottom:.28em;width:3px;border-radius:2px;
  background:linear-gradient(180deg,var(--accent2),rgba(18,136,155,.25))}
.h3 .hnum{font-family:var(--mono);font-size:12.5px;color:var(--accent);background:var(--soft);
  padding:1px 7px;border-radius:5px;font-weight:600}
.h4{font-size:15px;font-weight:650;color:var(--ink2);margin:24px 0 2px;display:flex;align-items:center;gap:8px}
.h4 .hnum{font-family:var(--mono);font-size:11.5px;color:var(--muted);background:#f1f5f8;padding:1px 6px;border-radius:4px}
.tg{flex:0 0 auto;order:-1;width:20px;height:20px;border:1px solid var(--line);background:#fff;border-radius:5px;
  cursor:pointer;position:relative;transition:.15s;opacity:0}
.h2:hover .tg,.h3:hover .tg,.chapter.is-collapsed .tg,.sec.is-collapsed .tg{opacity:1}
.tg:hover{border-color:var(--accent2);background:var(--soft2)}
.tg:before{content:"";position:absolute;left:6.5px;top:5px;width:4.5px;height:4.5px;border-right:1.5px solid #7c8b99;
  border-bottom:1.5px solid #7c8b99;transform:rotate(45deg);transition:.18s}
.is-collapsed>.h2 .tg:before,.is-collapsed>.h3 .tg:before{transform:rotate(-45deg)}
.is-collapsed>.chapter-body,.is-collapsed>.sec-body{display:none}
.is-collapsed>.h2{margin-bottom:4px;padding-top:14px;margin-top:22px}
.is-collapsed>.h3{margin-bottom:6px}
.sec-body,.sub-body{}

/* 要点 / 提示 */
.keypoint{margin:14px 0;padding:12px 16px 12px 16px;background:linear-gradient(90deg,var(--soft2),#fff 60%);
  border-left:3px solid var(--accent2);border-radius:0 8px 8px 0;color:var(--ink2);font-size:14.5px}
.keypoint strong{color:var(--accent);letter-spacing:1px}
.callout{margin:16px 0;padding:13px 18px;background:#f7fafb;border:1px solid #e2ebef;border-left:3px solid #9dc3cc;
  border-radius:0 8px 8px 0;color:var(--ink2)}
.callout.warn{background:#fdf8ef;border-color:#f0e0c4;border-left-color:#d99a2b;color:#6b4a10}
.callout.warn strong{color:#8a5a06}

/* 表格 */
.tw{margin:14px 0 18px;overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:#fff;
  scrollbar-width:thin}
.tw::-webkit-scrollbar{height:8px}
.tw::-webkit-scrollbar-thumb{background:#d8e0e7;border-radius:8px}
.tbl{width:100%;border-collapse:collapse;font-size:13.2px;line-height:1.65;min-width:520px}
.tbl.wide{min-width:840px}
.tbl th{position:sticky;top:0;background:#f2f6f8;color:#41525f;font-weight:650;text-align:left;
  padding:9px 12px;border-bottom:1px solid #dde5eb;white-space:nowrap;font-size:12.6px;letter-spacing:.2px;z-index:1}
.tbl td{padding:9px 12px;border-bottom:1px solid var(--line2);vertical-align:top;color:var(--ink2);
  word-break:keep-all;overflow-wrap:break-word}
.tbl tbody tr:last-child td{border-bottom:0}
.tbl tbody tr:nth-child(even){background:#fafcfd}
.tbl tbody tr:hover{background:var(--soft2)}
.tbl td:first-child{white-space:nowrap}
.tbl code{white-space:nowrap}
.partno{font-family:var(--mono);font-size:12.2px;white-space:nowrap;color:#25535f;letter-spacing:-.2px}
.pill{display:inline-block;font-size:11px;font-weight:700;line-height:1.5;padding:1px 7px;border-radius:5px;
  font-family:var(--mono);letter-spacing:.3px;white-space:nowrap}
.pill.p0{background:var(--redbg);color:var(--red);box-shadow:inset 0 0 0 1px #f6d3cf}
.pill.p1{background:var(--amberbg);color:var(--amber);box-shadow:inset 0 0 0 1px #f0dcbb}
.pill.p2{background:#eef3f9;color:#41586f;box-shadow:inset 0 0 0 1px #d9e3ee}
.pill.p3{background:#f2f4f6;color:#6b7a88;box-shadow:inset 0 0 0 1px #e2e7ec}
.lv{display:inline-block;font-family:var(--mono);font-size:11.5px;font-weight:700;padding:1px 7px;border-radius:5px;white-space:nowrap}
.lv-hi{background:#fdeceb;color:#b42318;box-shadow:inset 0 0 0 1px #f4cfcb}
.lv-midhi{background:#fdf4e5;color:#9a5b0b;box-shadow:inset 0 0 0 1px #efdcbd}
.lv-mid{background:#fff9e8;color:#8a6a13;box-shadow:inset 0 0 0 1px #efe3bd}
.lv-lo{background:#eef4f4;color:#4b6b6b;box-shadow:inset 0 0 0 1px #dbe6e6}
.idc{font-family:var(--mono);font-size:11.6px;color:#25535f;background:#eef6f7;padding:1px 6px;border-radius:4px;
  white-space:nowrap;box-shadow:inset 0 0 0 1px #d8e9ec}
pre.code{background:#0f2027;color:#d7e6ec;padding:14px 16px;border-radius:10px;overflow:auto;font-family:var(--mono);
  font-size:12.5px;line-height:1.6}
pre.code code{background:none;border:0;color:inherit;padding:0}

/* mermaid 图 */
.diagram{position:relative;margin:22px -20px 28px;padding:18px 12px 8px;border:1px solid #e2e9ee;border-radius:12px;
  background:linear-gradient(180deg,#fdfefe,#f8fbfc);transition:.18s}
.diagram:hover{border-color:#cfe0e6;box-shadow:0 6px 20px -14px rgba(15,107,122,.35)}
.diagram .mermaid{display:flex;justify-content:center;margin:0;overflow-x:auto;background:none;padding:0}
.diagram svg{max-width:100%;height:auto;display:block}
.dg-tools{position:absolute;right:10px;top:8px;opacity:0;transition:.15s;z-index:2}
.diagram:hover .dg-tools{opacity:1}
.dg-btn{font:inherit;font-size:11.5px;padding:3px 9px;border:1px solid #d5e2e8;background:#fff;color:var(--accent);
  border-radius:6px;cursor:pointer}
.dg-btn:hover{background:var(--soft);border-color:#bcd8df}
.toc-label,.toc-inline{display:none}
@media print{.toc-label{display:block}.toc-inline{display:block}}
figcaption{margin-top:10px;padding-top:8px;border-top:1px dashed #e4ebf0;text-align:center;color:var(--faint);
  font-size:12px;letter-spacing:.2px}
figcaption b{color:var(--accent);font-weight:650;font-family:var(--mono);font-size:11.5px}
.diagram.err{background:#fff8f7;border-color:#f2d6d2}
.diagram.err .mermaid{font-family:var(--mono);font-size:12px;white-space:pre-wrap;color:#8a3a30}

/* 灯箱 */
.lb{position:fixed;inset:0;z-index:100;background:rgba(13,26,34,.72);backdrop-filter:blur(3px);
  display:flex;flex-direction:column}
.lb[hidden]{display:none}
.lb-bar{display:flex;align-items:center;gap:10px;padding:10px 16px;background:rgba(255,255,255,.96);
  border-bottom:1px solid var(--line)}
.lb-bar .t{font-size:13px;color:var(--ink2);margin-right:auto}
.lb-bar button{font:inherit;font-size:12.5px;padding:5px 11px;border:1px solid var(--line);background:#fff;
  border-radius:7px;cursor:pointer;color:var(--ink2)}
.lb-bar button:hover{border-color:var(--accent2);color:var(--accent)}
.lb-stage{flex:1;overflow:auto;padding:22px}
.lb-canvas{background:#fff;border-radius:12px;padding:18px;width:max-content;margin:0 auto;min-width:min(92vw,900px)}
.lb-canvas svg{display:block;height:auto}

/* 返回顶部 */
.fab{position:fixed;right:26px;bottom:26px;width:40px;height:40px;border-radius:50%;border:1px solid var(--line);
  background:#fff;color:var(--accent);cursor:pointer;box-shadow:0 6px 18px -10px rgba(16,32,48,.4);
  opacity:0;pointer-events:none;transition:.2s;z-index:55}
.fab.show{opacity:1;pointer-events:auto}
.fab:before{content:"";position:absolute;left:14px;top:17px;width:11px;height:11px;border-left:2px solid currentColor;
  border-top:2px solid currentColor;transform:rotate(45deg)}

@media (max-width:1180px){.chips{display:none}}
@media (max-width:860px){
  .bsub{display:none}
  .topbar{gap:8px;padding:0 12px 0 10px}
  .brand{gap:7px;flex:1}
  .bt{font-size:13.5px}
}
@media (max-width:700px){
  .tools{display:none}
  .logo{width:23px;height:23px;border-radius:6px}
  .logo:after{inset:6px}
}
@media (max-width:980px){
  :root{--sbw:0px}
  .sidebar{transform:translateX(-100%);transition:.25s;width:288px;box-shadow:0 0 40px rgba(0,0,0,.18)}
  body.nav-open .sidebar{transform:none}
  .main{margin-left:0}
  .wrap{padding:18px 14px 90px}
  article{padding:26px 20px 34px;border-radius:12px}
  .hero-title{font-size:24px}
  .topbar .nav-toggle{display:inline-flex}
}
.nav-toggle{display:none;align-items:center;justify-content:center;width:32px;height:32px;border:1px solid var(--line);
  background:#fff;border-radius:8px;cursor:pointer;font-size:15px;color:var(--ink2)}

@media print{
  .topbar,.sidebar,.dg-tools,.tg,.fab,.lb{display:none!important}
  .main{margin:0;padding:0}
  .wrap{max-width:none;padding:0}
  article{border:0;box-shadow:none;padding:0}
  .is-collapsed>.chapter-body,.is-collapsed>.sec-body{display:block!important}
  .ni.collapsed>.nk{display:block}
  h2,h3{break-after:avoid}
  .diagram,.tw{break-inside:avoid}
  body{background:#fff;font-size:11.5pt}
}
</style>
</head>
<body>

<header class="topbar">
  <button class="nav-toggle" id="navToggle" aria-label="导航">☰</button>
  <div class="brand">
    <div class="logo"></div>
    <div style="min-width:0">
      <div class="bt">SKU2 双鉴存在传感器 · 产品需求文档</div>
      <div class="bsub">LANCHAO ENERGY IoT · PRD</div>
    </div>
  </div>
  <div class="chips">
    <span class="chip on">V3.0</span>
    <span class="chip">评审稿</span>
    <span class="chip">LC-S-MTS03-PR24-11-001</span>
    <span class="chip">大陆 / 香港</span>
  </div>
  <div class="tools">
    <button class="tool" id="expandAll">展开正文</button>
    <button class="tool" id="collapseAll">收起正文</button>
    <button class="tool" id="printBtn">打印</button>
  </div>
  <div class="prog" id="prog"></div>
</header>

<aside class="sidebar">
  <div class="sb-head">
    <div class="sb-title">文档导航</div>
    <div class="sb-stats">__NCH__ 章 · __NSEC__ 节 · __NDG__ 图</div>
    <div class="sb-search">
      <span class="ico"></span>
      <input id="q" type="search" placeholder="搜索章节 / 编号（按 / 聚焦）" autocomplete="off">
      <button class="clr" id="qclr" aria-label="清空">×</button>
    </div>
    <div class="sb-acts">
      <button id="navExpand">展开目录</button>
      <button id="navCollapse">收起目录</button>
    </div>
  </div>
  <nav class="toc" id="toc">__NAV__</nav>
</aside>

<main class="main">
  <div class="wrap"><article id="doc">
__ARTICLE__
  </article></div>
</main>

<button class="fab" id="fab" aria-label="返回顶部"></button>

<div class="lb" id="lb" hidden>
  <div class="lb-bar">
    <span class="t" id="lbTitle">图表</span>
    <button id="lbFit">适应宽度</button>
    <button id="lbOrig">100%</button>
    <button id="lbIn">放大 +</button>
    <button id="lbOut">缩小 −</button>
    <button id="lbClose">关闭</button>
  </div>
  <div class="lb-stage" id="lbStage"><div class="lb-canvas" id="lbCanvas"></div></div>
</div>

<script>__MERMAID__</script>
<script>
(function(){
  "use strict";
  var $=function(s,r){return (r||document).querySelector(s)};
  var $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};

  /* ---------- 1. mermaid 渲染 ---------- */
  var mermaidBoxes=$$('.mermaid');
  if(window.mermaid){
    mermaid.initialize({
      startOnLoad:false,
      securityLevel:'loose',
      theme:'base',
      themeVariables:{
        fontFamily:'-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Source Han Sans SC",sans-serif',
        fontSize:'16px',
        primaryColor:'#e8f1f5', primaryTextColor:'#16202b', primaryBorderColor:'#7fa6b5',
        secondaryColor:'#f1f5f9', secondaryTextColor:'#33414f', secondaryBorderColor:'#b9c9d4',
        tertiaryColor:'#fbfdfe', tertiaryTextColor:'#33414f', tertiaryBorderColor:'#d6e0e6',
        lineColor:'#8aa0ae', textColor:'#16202b',
        clusterBkg:'#f7fafb', clusterBorder:'#d6e0e6',
        edgeLabelBackground:'#ffffff',
        noteBkgColor:'#fdf8ef', noteBorderColor:'#e6d3b3', noteTextColor:'#6b4a10',
        activationBkgColor:'#e8f1f5', activationBorderColor:'#7fa6b5'
      },
      flowchart:{curve:'basis',htmlLabels:true,useMaxWidth:true,padding:18,nodeSpacing:42,rankSpacing:52},
      sequence:{useMaxWidth:true,wrap:true,diagramMarginX:16,diagramMarginY:12,boxMargin:8},
      state:{useMaxWidth:true},
      er:{useMaxWidth:true}
    });
    var mmTasks=[];
    mermaidBoxes.forEach(function(el,idx){
      var fig=el.closest('.diagram');
      var src=el.textContent;
      var id='mmd-'+(idx+1);
      try{
        mmTasks.push(mermaid.render(id,src).then(function(res){
          el.innerHTML=res.svg;
          var svg=el.querySelector('svg');
          if(svg){
            svg.removeAttribute('height');
            svg.style.height='auto';
            svg.style.width='100%';
            svg.style.maxWidth='100%';
          }
        }).catch(function(e){fail(el,e);}));
      }catch(e){fail(el,e);}
    });
    Promise.allSettled(mmTasks).then(function(){
      alignHash();
      setTimeout(alignHash,150);
      setTimeout(alignHash,600);
    });
  }
  function fail(el,e){
    var fig=el.closest('.diagram');
    if(fig) fig.classList.add('err');
    el.textContent='图表渲染失败：'+(e&&e.message?e.message:'未知错误')+'\n\n'+el.textContent;
  }

  /* ---------- 2. 正文折叠 ---------- */
  $$('.chapter, .sec').forEach(function(sec){
    var h=sec.querySelector(':scope > .h2, :scope > .h3');
    var btn=h&&h.querySelector('.tg');
    if(!btn) return;
    sec.classList.add('foldable');
    btn.addEventListener('click',function(ev){
      ev.preventDefault();ev.stopPropagation();
      sec.classList.toggle('is-collapsed');
      btn.setAttribute('aria-label',sec.classList.contains('is-collapsed')?'展开本章节':'折叠本章节');
    });
  });
  function setAll(collapse){
    $$('.chapter, .sec').forEach(function(s){s.classList.toggle('is-collapsed',collapse)});
  }
  $('#expandAll').addEventListener('click',function(){setAll(false)});
  $('#collapseAll').addEventListener('click',function(){setAll(true)});
  $('#printBtn').addEventListener('click',function(){window.print()});

  /* ---------- 3. 目录 ---------- */
  var toc=$('#toc');
  toc.addEventListener('click',function(e){
    var c=e.target.closest('.caret');
    if(c){e.preventDefault();c.closest('.ni').classList.toggle('collapsed');return;}
    var a=e.target.closest('a.nl');
    if(!a) return;
    var id=a.getAttribute('href').slice(1);
    var target=document.getElementById(id);
    if(!target) return;
    e.preventDefault();
    // 展开目标所在的所有折叠节
    var p=target;
    while(p&&p!==document.body){
      if(p.classList&&(p.classList.contains('chapter')||p.classList.contains('sec'))){
        p.classList.remove('is-collapsed');
      }
      p=p.parentElement;
    }
    var y=target.getBoundingClientRect().top+window.pageYOffset-72;
    window.scrollTo({top:y,behavior:'smooth'});
    history.replaceState(null,'','#'+id);
    if(window.innerWidth<=980) document.body.classList.remove('nav-open');
  });
  function navSetAll(open){
    $$('#toc .ni').forEach(function(ni){
      var has=ni.querySelector(':scope > .nk');
      if(has) ni.classList.toggle('collapsed',!open);
    });
  }
  $('#navExpand').addEventListener('click',function(){navSetAll(true)});
  $('#navCollapse').addEventListener('click',function(){navSetAll(false)});

  /* ---------- 4. 搜索过滤 ---------- */
  var q=$('#q'),qclr=$('#qclr');
  function filterNav(){
    var v=q.value.trim().toLowerCase();
    qclr.style.display=v?'block':'none';
    $$('#toc .nl').forEach(function(a){
      var hit=!v||a.textContent.toLowerCase().indexOf(v)>-1;
      a.classList.toggle('hide',!hit);
    });
    $$('#toc .ni').reverse().forEach(function(ni){
      var vis=$$('.nl',ni).filter(function(x){return !x.classList.contains('hide')}).length;
      ni.classList.toggle('hide',vis===0);
      if(v&&vis>0){
        if(ni.querySelector(':scope > .nk')) ni.classList.remove('collapsed');
      }
      if(vis>0){
        var own=ni.querySelector(':scope > .nr > .nl');
        if(own) own.classList.remove('hide');
      }
      var p=ni.parentElement;
      if(v&&vis>0){ while(p&&p!==toc){ if(p.classList&&p.classList.contains('ni')){p.classList.remove('hide');p.classList.remove('collapsed');} p=p.parentElement; } }
    });
  }
  q.addEventListener('input',filterNav);
  qclr.addEventListener('click',function(){q.value='';q.dispatchEvent(new Event('input'));q.focus();});
  document.addEventListener('keydown',function(e){
    if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}
    if(e.key==='Escape'){closeLb();document.body.classList.remove('nav-open');}
  });

  /* ---------- 5. 滚动：进度 + 高亮 ---------- */
  var heads=$$('#doc .chapter, #doc .sec, #doc .sub');
  var links={};
  $$('#toc a.nl').forEach(function(a){links[a.getAttribute('href').slice(1)]=a;});
  var prog=$('#prog'),fab=$('#fab'),ticking=false;
  function onScroll(){
    if(ticking)return;ticking=true;
    requestAnimationFrame(function(){
      var st=window.pageYOffset;
      var h=document.documentElement.scrollHeight-window.innerHeight;
      prog.style.width=(h>0?Math.min(100,st/h*100):0)+'%';
      fab.classList.toggle('show',st>600);
      var cur=null;
      for(var i=0;i<heads.length;i++){
        if(heads[i].getBoundingClientRect().top<=120) cur=heads[i].id; else break;
      }
      if(!cur&&heads.length) cur=heads[0].id;
      if(cur&&links[cur]){
        $$('#toc a.nl.active').forEach(function(a){a.classList.remove('active')});
        var a=links[cur];a.classList.add('active');
        var ni=a.closest('.ni');
        while(ni&&ni!==toc){if(ni.classList&&ni.parentElement&&ni.parentElement.classList.contains('nk')){
          var par=ni.parentElement.closest('.ni'); if(par) par.classList.remove('collapsed');}
          ni=ni.parentElement;}
        var r=a.getBoundingClientRect(),tr=toc.getBoundingClientRect();
        if(r.top<tr.top+8||r.bottom>tr.bottom-8) a.scrollIntoView({block:'nearest'});
      }
      ticking=false;
    });
  }
  window.addEventListener('scroll',onScroll,{passive:true});
  window.addEventListener('resize',onScroll);

  /* ---------- 6. 图表放大 ---------- */
  var lb=$('#lb'),lbCanvas=$('#lbCanvas'),lbTitle=$('#lbTitle'),lbStage=$('#lbStage');
  var curSvg=null,baseW=0,scale=1;
  function openLb(fig){
    var svg=fig.querySelector('svg');
    if(!svg) return;
    var cap=fig.querySelector('figcaption');
    lbTitle.textContent=cap?cap.textContent:'图表';
    lbCanvas.innerHTML='';
    var clone=svg.cloneNode(true);
    clone.removeAttribute('style');
    var vb=svg.viewBox&&svg.viewBox.baseVal;
    baseW=(vb&&vb.width)?vb.width:(svg.getBoundingClientRect().width||900);
    var h=(vb&&vb.height)?vb.height:baseW*0.6;
    clone.setAttribute('viewBox','0 0 '+baseW+' '+h);
    clone.setAttribute('width',baseW);
    clone.setAttribute('height',h);
    clone.style.width='100%';clone.style.height='auto';
    lbCanvas.appendChild(clone);
    curSvg=clone;scale=1;
    lb.hidden=false;document.body.style.overflow='hidden';
    requestAnimationFrame(fit);
  }
  function fit(){
    if(!curSvg)return;
    var avail=lbStage.clientWidth-44;
    lbCanvas.style.width=Math.max(320,Math.min(avail,1400))+'px';
    curSvg.style.width='100%';scale=1;
  }
  function setScale(s){
    if(!curSvg)return;
    scale=Math.max(.4,Math.min(4,s));
    curSvg.style.width=(baseW*scale)+'px';
    lbCanvas.style.width='max-content';
  }
  function closeLb(){if(lb.hidden)return;lb.hidden=true;document.body.style.overflow='';lbCanvas.innerHTML='';curSvg=null;}
  $$('.diagram').forEach(function(fig){
    var btn=fig.querySelector('.dg-btn');
    if(btn) btn.addEventListener('click',function(){openLb(fig)});
    fig.addEventListener('dblclick',function(){openLb(fig)});
  });
  $('#lbClose').addEventListener('click',closeLb);
  lb.addEventListener('click',function(e){if(e.target===lb||e.target===lbStage)closeLb();});
  $('#lbFit').addEventListener('click',fit);
  $('#lbOrig').addEventListener('click',function(){setScale(1)});
  $('#lbIn').addEventListener('click',function(){setScale(scale*1.25)});
  $('#lbOut').addEventListener('click',function(){setScale(scale/1.25)});
  $('#lbStage').addEventListener('wheel',function(e){
    if(!e.ctrlKey)return;e.preventDefault();setScale(scale*(e.deltaY<0?1.1:0.9));
  },{passive:false});

  /* ---------- 7. 其他 ---------- */
  $('#fab').addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'})});
  $('#navToggle').addEventListener('click',function(){document.body.classList.toggle('nav-open')});
  window.addEventListener('beforeprint',function(){setAll(false)});
  function alignHash(){
    if(!location.hash) return;
    var id=decodeURIComponent(location.hash.slice(1));
    var t=document.getElementById(id);
    if(!t) return;
    var p=t;
    while(p&&p!==document.body){
      if(p.classList&&(p.classList.contains('chapter')||p.classList.contains('sec'))) p.classList.remove('is-collapsed');
      p=p.parentElement;
    }
    var y=t.getBoundingClientRect().top+window.pageYOffset-70;
    window.scrollTo({top:Math.max(0,y),behavior:'auto'});
    // 图渲染会改变高度，循环校正直到位置稳定
    if(hashTimer) clearInterval(hashTimer);
    var stable=0, tries=0;
    hashTimer=setInterval(function(){
      tries++;
      var top=t.getBoundingClientRect().top;
      if(Math.abs(top-70)<4){
        stable++;
        if(stable>=2){clearInterval(hashTimer);hashTimer=null;}
      }else{
        stable=0;
        window.scrollTo({top:Math.max(0,top+window.pageYOffset-70),behavior:'auto'});
      }
      if(tries>26){clearInterval(hashTimer);hashTimer=null;}
    },130);
  }
  var hashTimer=null;
  window.addEventListener('load',function(){alignHash();setTimeout(alignHash,250);setTimeout(alignHash,900);});
  window.addEventListener('hashchange',alignHash);
  alignHash();
  onScroll();
})();
</script>
</body>
</html>
"""

html_out = (TPL.replace('__TITLE__', 'SKU2 双鉴存在传感器 · 产品需求文档 V3.0')
               .replace('__NAV__', nav_html)
               .replace('__ARTICLE__', article)
               .replace('__NCH__', str(n_ch))
               .replace('__NSEC__', str(n_sec))
               .replace('__NDG__', str(diag_no))
               .replace('__MERMAID__', mermaid_js))

open(OUT, 'w', encoding='utf-8').write(html_out)
print('OUT :', OUT)
print('size: %.2f MB' % (len(html_out.encode('utf-8')) / 1048576))
print('chapters=%d sections=%d diagrams=%d tables=%d' % (
    n_ch, n_sec, diag_no, article.count('<table class="tbl')))
