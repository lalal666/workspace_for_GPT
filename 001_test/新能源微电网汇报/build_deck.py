import sys, math, json, re, zipfile
from pathlib import Path
sys.path.insert(0, '/tmp/microgrid_ppt_libs')
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_MARK, XL_DATA_LABEL_POSITION
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.chart.data import CategoryChartData
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
prs = Presentation()
prs.slide_width = Inches(13.333333)
prs.slide_height = Inches(7.5)
prs.core_properties.title = '新能源微电网：市场洞察与技术趋势分析'
prs.core_properties.subject = '国内与全球微电网市场、技术趋势与产业机会'
prs.core_properties.author = '产业战略研究'
prs.core_properties.keywords = '微电网,构网型逆变器,EMS,数字孪生,V2G,源网荷储'
FONT = 'Microsoft YaHei'
FP = '/mnt/c/Windows/Fonts/msyh.ttc'
FB = '/mnt/c/Windows/Fonts/msyhbd.ttc'
NAVY='10283F'; INK='143047'; TEAL='00A68B'; LIME='81D9BE'; ORANGE='F3AA57'; BLUE='3E82C4'; WHITE='FFFFFF'; BG='F4F7FA'; GRAY='667B8A'; LINE='D9E4EB'; PALE='E9F5F1'; DARKCARD='19374F'; RED='B95F51'
slides=[]; notes=[]; previews=[]; warnings=[]

def rgb(c): return RGBColor.from_string(c)
def rect(s,x,y,w,h,fill,line=None,radius=False):
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x),Inches(y),Inches(w),Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb=rgb(fill)
    if line: sh.line.color.rgb=rgb(line); sh.line.width=Pt(.8)
    else: sh.line.fill.background()
    s._draw.append(('rect',x,y,w,h,fill,line,radius))
    return sh

def line(s,x1,y1,x2,y2,c=LINE,width=1.2,dash=False):
    sh=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1),Inches(y1),Inches(x2),Inches(y2))
    sh.line.color.rgb=rgb(c); sh.line.width=Pt(width)
    if dash: sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    s._draw.append(('line',x1,y1,x2,y2,c,width,dash))
    return sh

def text(s,x,y,w,h,t,size=18,c=INK,bold=False,align='left',margin=0):
    sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=sh.text_frame
    tf.clear(); tf.word_wrap=True
    tf.margin_left=tf.margin_right=Inches(margin); tf.margin_top=tf.margin_bottom=0
    for i,st in enumerate(t.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text=st; p.font.name=FONT; p.font.size=Pt(size); p.font.color.rgb=rgb(c); p.font.bold=bold
        p.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[align]
        p.space_before=Pt(0); p.space_after=Pt(3); p.line_spacing=1.15
        p._p.get_or_add_pPr()
        for run in p.runs:
            from pptx.oxml.xmlchemy import OxmlElement
            rpr=run._r.get_or_add_rPr()
            ea=OxmlElement('a:ea');ea.set('typeface',FONT);rpr.append(ea)
    s._draw.append(('text',x,y,w,h,t,size,c,bold,align))
    return sh

def badge(s,x,y,w,t,c=TEAL,bg=PALE):
    rect(s,x,y,w,.3,bg,radius=True);text(s,x,y+.035,w,.23,t,10,c,True,'center')

def base(n,title,sub,section='MARKET INTELLIGENCE',dark=False):
    s=prs.slides.add_slide(prs.slide_layouts[6]);s._draw=[];s._dark=dark
    s.background.fill.solid();s.background.fill.fore_color.rgb=rgb(NAVY if dark else BG)
    s._draw.append(('bg',NAVY if dark else BG))
    col=WHITE if dark else INK
    rect(s,.55,.38,.09,.25,TEAL)
    text(s,.76,.36,10,.3,section,10,LIME if dark else TEAL,True)
    text(s,.6,.85,12.1,.62,title,28,col,True)
    text(s,.62,1.56,12.0,.5,sub,12.5,'B0C9D7' if dark else GRAY)
    line(s,.6,6.97,12.73,6.97,'35536A' if dark else LINE,.7)
    text(s,.62,7.08,11,.2,'新能源微电网  /  产业战略研究  /  2026.10',8.5,'94B0C2' if dark else GRAY)
    text(s,12.02,7.04,.7,.3,f'{n:02d} / 16',10,LIME if dark else TEAL,True,'right')
    slides.append(s);return s

def footer(s,t):text(s,.63,6.55,12.05,.31,t,8.4,'A9C0CF' if s._dark else GRAY)

def card(s,x,y,w,h,num,title,body,dark=False,accent=TEAL):
    rect(s,x,y,w,h,DARKCARD if dark else WHITE,radius=True)
    rect(s,x,y,.055,h,accent)
    text(s,x+.2,y+.18,w-.4,.35,num,12,accent,True)
    text(s,x+.2,y+.66,w-.4,.45,title,20,WHITE if dark else INK,True)
    text(s,x+.2,y+1.24,w-.4,h-1.37,body,14,'BDD0DC' if dark else GRAY)

def node(s,x,y,w,h,title,sub='',color=TEAL,dark=False):
    rect(s,x,y,w,h,DARKCARD if dark else WHITE,color,radius=True)
    text(s,x+.1,y+.13,w-.2,.38,title,16,WHITE if dark else INK,True,'center')
    if sub:text(s,x+.1,y+.58,w-.2,h-.63,sub,11,'BDD0DC' if dark else GRAY,False,'center')

def note(s,title,body,chart,image,sources=[]):
    t=f'页面标题：{title}\n\n正文要点：\n'+'\n'.join('• '+b for b in body)+f'\n\n【图表建议】：\n{chart}\n\n【配图描述】：\n{image}'
    if sources:t+='\n\n资料来源与口径：\n'+'\n'.join(sources)
    s.notes_slide.notes_text_frame.text=t
    notes.append(t)

def native_line(s,x,y,w,h,categories,series,maxval,step,unit,dark=False):
    data=CategoryChartData();data.categories=categories
    for name,vals,c in series:data.add_series(name,vals)
    chart=s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS,Inches(x),Inches(y),Inches(w),Inches(h),data).chart
    from pptx.oxml.xmlchemy import OxmlElement
    for parent in [chart._chartSpace, chart._chartSpace.chart.plotArea]:
        sp=OxmlElement('c:spPr'); sf=OxmlElement('a:solidFill'); sr=OxmlElement('a:srgbClr'); sr.set('val',NAVY if dark else BG);sf.append(sr);sp.append(sf);parent.insert_element_before(sp,'c:txPr','c:externalData','c:printSettings','c:userShapes','c:extLst')
    plot=chart.plots[0];plot.has_data_labels=True
    plot.data_labels.position=XL_DATA_LABEL_POSITION.ABOVE
    plot.data_labels.font.name=FONT;plot.data_labels.font.size=Pt(10);plot.data_labels.font.color.rgb=rgb('C7E4D9' if dark else GRAY)
    plot.data_labels.number_format='0.#'
    chart.has_legend=True;chart.legend.position=XL_LEGEND_POSITION.BOTTOM;chart.legend.include_in_layout=False
    chart.legend.font.name=FONT;chart.legend.font.size=Pt(10);chart.legend.font.color.rgb=rgb(WHITE if dark else GRAY)
    chart.font.name=FONT;chart.font.size=Pt(11)
    for ax in [chart.category_axis,chart.value_axis]:
        ax.tick_labels.font.name=FONT;ax.tick_labels.font.size=Pt(11);ax.tick_labels.font.color.rgb=rgb('B5CBD8' if dark else GRAY)
        ax.format.line.color.rgb=rgb('436075' if dark else LINE)
        ax.major_tick_mark=XL_TICK_MARK.NONE;ax.minor_tick_mark=XL_TICK_MARK.NONE
    chart.value_axis.minimum_scale=0;chart.value_axis.maximum_scale=maxval;chart.value_axis.major_unit=step
    chart.value_axis.has_major_gridlines=True;chart.value_axis.major_gridlines.format.line.color.rgb=rgb('2C485F' if dark else LINE)
    chart.category_axis.has_major_gridlines=False
    for se,(_,vals,c) in zip(chart.series,series):
        se.format.line.color.rgb=rgb(c);se.format.line.width=Pt(2.5)
        se.marker.style=XL_MARKER_STYLE.CIRCLE;se.marker.size=7;se.marker.format.fill.solid();se.marker.format.fill.fore_color.rgb=rgb(c);se.marker.format.line.color.rgb=rgb(c)
    s._draw.append(('chart',x,y,w,h,categories,series,maxval,step,unit,dark))
    text(s,x+.02,y-.28,w,.24,unit,10,'B5CBD8' if dark else GRAY)
    return chart

SOURCES={
'global':'Grand View Research, Microgrid Market 2026–2033：https://www.grandviewresearch.com/industry-analysis/microgrid-market',
'policy':'国家发展改革委、国家能源局《关于促进电网高质量发展的指导意见》：https://www.ndrc.gov.cn/xwdt/tzgg/202512/t20251231_1402950.html',
'direct':'《关于有序推动绿电直连发展有关事项的通知》：https://zfxxgk.ndrc.gov.cn/web/iteminfo.jsp?id=20511',
'doe':'美国能源部 Microgrid Systems：https://www.energy.gov/oe/microgrid-systems',
'gfm':'NREL, Research Roadmap on Grid-Forming Inverters：https://www.nrel.gov/news/program/2020/technical-roadmap-guides-research-direction-grid-forming-inverters',
'v2g':'首批车网互动规模化应用试点通知：https://www.ndrc.gov.cn/xwdt/tzgg/202504/t20250402_1396960_ext.html',
'ems':'Schneider EcoStruxure Microgrid Advisor：https://www.se.com/us/en/product-range/65896-ecostruxure-microgrid-advisor/',
'siemens':'Siemens SICAM Microgrid Control：https://www.siemens.com/en-us/products/microgrids/sicam-microgrid-control/',
'acrel':'安科瑞微电网能量管理系统：https://ems.acrel.cn/emsnx/570',
'sungrow':'阳光电源构网测试资料：https://www.sungrowpower.com/en/beyond-simulation-sungrow-completes-world-s-first-large-scale-full-condition-grid-forming-extreme-test',
'epc':'中国电建微电网采购案例：https://ec.powerchina.cn/bidBulletin/2025-08-21/641432.html'
}

# 01 — Cover
s=base(1,'','',section='ENERGY TRANSITION  /  STRATEGY BRIEF',dark=True)
text(s,.65,1.4,7.4,.95,'新能源微电网',44,WHITE,True)
text(s,.68,2.48,7.5,.65,'市场洞察与技术趋势分析',29,WHITE,True)
text(s,.71,3.43,6.5,.75,'从风光储设备集成\n走向可独立运行、可优化调度的能源系统',18,'BED2DE')
for xx,lab,ww in [(.72,'国内 + 全球',1.55),(2.45,'并网 + 孤岛',1.6),(4.22,'2027—2031',1.7)]:badge(s,xx,4.85,ww,lab,LIME,DARKCARD)
text(s,.73,5.63,6.4,.45,'面向产业客户、设备企业与投资决策者',13,'A9C0CF')
# Editable network motif
line(s,8.1,4.0,11.8,4.0,TEAL,3)
for x,y,t,sub in [(8.0,2.1,'风 / 光','清洁电源'),(10.55,2.1,'公共电网','双向交互'),(8.0,4.7,'储能','功率 + 能量'),(10.55,4.7,'负荷 / V2G','用能与调节')]:
    line(s,x+1, y+(.95 if y<4 else 0),x+1,4,TEAL,1.6)
    node(s,x,y,2,1.05,t,sub,TEAL,True)
node(s,9.15,3.45,1.7,1.08,'微电网','统一可控',LIME,True)
note(s,'新能源微电网：市场洞察与技术趋势分析',['国内与全球市场；面向B端产业汇报。','分析时点：2026年10月；机会展望：2027—2031年。'], '定性架构框图，无数值坐标。中心微电网连接风光、储能、公共电网及负荷/V2G；绿色为能源交互。', '16∶9横版。右侧写实工业园区鸟瞰：屋顶光伏、远景风机、近景储能集装箱与充电车位，以细线连接。左侧45%深蓝渐变留白用于标题。深蓝、青绿、银灰色调，清晨自然光，无Logo、无内嵌文字。当前PPT以可编辑系统框图代替图片。')

# 02 — Agenda
s=base(2,'目录：从市场空间到技术能力，再到商业兑现','16页 · 三个分析层次 · 一条决策主线',section='CONTENTS')
card(s,.65,2.25,3.9,3.65,'01 / 第3—8页','市场与产业环境','定义与分类\n全球与中国市场\n应用场景、竞争格局、PEST',accent=BLUE)
card(s,4.72,2.25,3.9,3.65,'02 / 第9—12页','架构与技术演进','源网荷储架构\n主流技术栈与构网控制\nAI、数字孪生、多微网协同',accent=TEAL)
card(s,8.79,2.25,3.9,3.65,'03 / 第13—16页','商业化与战略选择','行业痛点与收益验证\n未来3—5年机会\n核心判断与Q&A',accent=ORANGE)
footer(s,'叙事主线：市场需求 → 场景与竞争 → 技术实现 → 商业兑现')
note(s,'目录',['第3—8页：定义分类、全球与中国市场、应用需求、竞争格局与PEST。','第9—12页：源网荷储架构、主流技术栈、构网型逆变器与智能调度。','第13—16页：瓶颈、机会、核心判断与讨论。'],'定性架构框图。无坐标轴；三模块横向递进。蓝色市场、绿色技术、橙色商业；维度为章节顺序、关键问题、页码范围。','浅灰白底。底部连续等距微缩场景：左侧园区与地球，中间储能和控制中心，右侧项目交付团队。统一视角、柔和阴影、蓝绿配色，上半部留白放目录。')

# 03 — Definition
s=base(3,'微电网定义、分类与运行模式','明确电气边界 + 源荷储协同 + 统一可控；并网型微网也可进入临时孤岛状态',section='01 / MARKET & APPLICATIONS')
rect(s,.65,2.2,5.95,3.65,WHITE,radius=True);rect(s,6.78,2.2,5.9,3.65,WHITE,radius=True)
badge(s,.9,2.44,1.2,'并网型',BLUE,'EAF1F8');badge(s,7.02,2.44,1.2,'独立型',TEAL,PALE)
node(s,.95,3.1,1.5,1.02,'公共电网','外部参考',BLUE);node(s,3.45,3.1,2.73,1.02,'园区微电网','源 · 网 · 荷 · 储',TEAL)
line(s,2.45,3.62,3.45,3.62,BLUE,2);text(s,2.48,3.15,.95,.3,'PCC开关',10,GRAY,False,'center')
text(s,.96,4.48,5.2,.6,'并网优化购售电与消纳\n具备配置后可解列保供',16,INK)
node(s,7.07,3.1,2.1,1.02,'本地构网电源','同步机 / 构网逆变器');node(s,9.85,3.1,2.45,1.02,'独立微电网','本地功率与能量平衡')
line(s,9.17,3.62,9.85,3.62,TEAL,2)
text(s,7.1,4.48,5.1,.6,'长期脱离公共电网\n保供、备用与燃料替代优先',16,INK)
rect(s,.65,6.06,12.03,.37,PALE,radius=True);text(s,.88,6.11,11.5,.27,'运行流程：并网 → 解列 → 孤岛运行 → 同期校验 → 重并网',12,TEAL,True,'center')
footer(s,'来源：美国能源部。风光储简单组合不自动具备孤岛运行能力；切换性能需结合保护与负荷要求验证。')
note(s,'微电网定义、分类与运行模式（并网/孤岛）',['在明确电气边界内，将分布式电源、储能与负荷组织成统一可控系统。','并网型正常接入公共电网，具备相应配置后可解列进入孤岛。','独立型长期离网，依靠本地电源与储能平衡。','孤岛既是独立系统特征，也可为并网微网的临时运行状态。'],'定性架构框图；无数值轴。比较公共电网连接、构网来源、控制目标、供电保障。蓝线表示并网连接，绿线表示本地能源连接；PCC标记连接边界。','左右分屏等距插画：左为接入配电网的工业园区，突出入口开关站；右为远离大陆的海岛，配置风光储与备用机组。蓝线表示并网，绿线表示本地循环；独立海岛不画海底电缆。',[SOURCES['doe']])

# 04 — Global quantitative
s=base(4,'全球微电网市场规模与增长预测','增长方向明确；全口径微电网市场不能直接等同于新能源微电网市场',section='01 / GLOBAL MARKET',dark=True)
text(s,.7,2.25,3.2,.38,'2026年机构预测',13,'B6CEDB')
text(s,.68,2.78,3.5,.8,'1,152',45,WHITE,True);text(s,.74,3.67,2.8,.35,'亿美元',17,LIME)
text(s,.73,4.39,2.8,.6,'19.7%',31,LIME,True)
text(s,.74,5.04,3.05,.75,'2026—2033年\n机构预测复合增速',13,'B6CEDB')
native_line(s,4.05,2.5,8.55,3.68,['2025','2026','2027','2028','2029','2030','2031'],[('市场规模',[99.8,115.2,137.9,165.1,197.6,236.5,283.1],LIME)],300,100,'市场规模 / 十亿美元',True)
text(s,4.55,6.04,7.65,.32,'2025 历史估计  |  2026 机构预测  |  2027—2031 本稿推算',10,'B6CEDB')
footer(s,'来源：Grand View Research。推算按2026年115.2十亿美元及19.7%增速；全口径包含燃气、柴油等资源。')
note(s,'全球微电网市场规模与增长预测',['GVR估计2025年全球市场998亿美元，预测2026年1,152亿美元。','机构预测2026—2033年复合增长19.7%。','驱动：供电韧性、本地能源开发与新能源接入。','统计包含燃气、柴油等资源，不能直接当作新能源微电网规模。'],'定量折线图。横轴2025—2031年，纵轴市场规模（十亿美元，0—300）。序列99.8、115.2、137.9、165.1、197.6、236.5、283.1。图例为市场规模。2025为机构历史估计，2026为机构预测，2027—2031为本稿按19.7%推算，非机构逐年公布值。','低饱和世界地图背景，北美点缀园区与关键设施，欧洲点缀社区能源，亚洲点缀工厂与海岛。浅灰大陆、深蓝海岸线、青绿节点；节点不表示份额，右侧留折线图区域。',[SOURCES['global']])

# 05 — China estimates
s=base(5,'中国微电网市场：政策驱动 + 市场空间','聚焦1—10MW级新增新能源微网；以透明假设估算可服务的年度建设空间',section='01 / CHINA MARKET')
native_line(s,.8,2.58,7.25,3.58,['2026','2031'],[('保守',[100,256],GRAY),('基准',[160,400],TEAL),('积极',[240,608],BLUE)],700,100,'年度新增投资 / 亿元')
rect(s,8.37,2.21,4.25,3.98,WHITE,radius=True)
text(s,8.62,2.45,3.75,.4,'政策打开应用入口',19,INK,True)
text(s,8.62,3.08,3.7,.8,'主配微协同建设\n绿电直连与就近消纳',16,GRAY)
line(s,8.62,4.04,12.3,4.04,LINE)
text(s,8.62,4.28,3.7,.4,'基准情景：160 → 400亿元',18,TEAL,True)
text(s,8.62,4.93,3.7,.95,'2026：800个 × 2,000万元\n2031：2,500个 × 1,600万元\n项目数量与投资额均为模型假设',12,GRAY)
footer(s,'来源：发改能源〔2025〕1710号、650号；图表为自建情景模型，非官方统计，不用于计算中国全球市场占比。')
note(s,'中国微电网市场：政策驱动+市场空间',['主配微协同、绿电直连与源网荷储调控提供发展入口。','工业园区、偏远供电和关键负荷韧性是需求重点。','模型聚焦1—10MW级新增新能源微网；基准年度建设额由160亿元增至400亿元。'],'定量情景折线图。横轴2026、2031年；纵轴年度新增项目投资额（亿元），零起点；灰/绿/蓝为保守/基准/积极。2026年假设500/800/1200个项目×2000万元=100/160/240亿元。2031年假设1600/2500/3800个×1600万元=256/400/608亿元。含项目内电源、储能、配电和控制，不含大型基地、土地和运营收入；单价下降代表设备降本与交付标准化假设。非官方统计，与全球口径不同。','工业园区俯视图，厂房、变电站、光伏车棚、储能紧凑布局。左上以半透明政策文件图标引出建设，右下能源管理中心。白底蓝绿，橙色强调储能，中部留图表位置，不绘制政策印章。',[SOURCES['policy'],SOURCES['direct']])

# 06 — Applications
s=base(6,'下游应用场景拆解：同一能力，对应不同客户价值','优先识别客户愿意付费的问题，再确定能源与控制配置',section='01 / APPLICATIONS')
scene=[('工业园区','并网为主','光储 + EMS','电费优化\n绿电消费\n关键产线保供',BLUE),('海岛','独立 / 弱网','风光储 + 备用','降低燃料依赖\n提高供电稳定\n减少运维难度',TEAL),('矿区','独立 / 弱网','风光储 + 机组','燃料替代\n生产连续性\n大负荷协调',TEAL),('数据中心','并网 + 备用','微网 + UPS','连续供电\n电能质量\n绿电使用',BLUE),('乡村','并网 / 独立','分布式光储','就地消纳\n简便运维\n可负担供电',ORANGE)]
for i,(title,mode,config,body,c) in enumerate(scene):
    x=.65+i*2.43;rect(s,x,2.25,2.27,3.85,WHITE,radius=True)
    rect(s,x,2.25,2.27,.07,c);text(s,x+.17,2.56,1.94,.45,title,21,INK,True)
    badge(s,x+.17,3.16,1.91,mode,c,'EDF3F6')
    text(s,x+.17,3.77,1.94,.5,config,14,c,True)
    line(s,x+.17,4.41,x+2.1,4.41,LINE)
    text(s,x+.17,4.66,1.95,1.1,body,14,GRAY)
footer(s,'定性场景拆解，不表示市场份额。数据中心的微网、UPS和备用电源需按连续供电目标协调设计。')
note(s,'下游应用场景拆解（工业园区、海岛、矿区、数据中心、乡村）',['工业园区：并网为主，电费优化、绿电消费与保供。','海岛与矿区：独立或弱网，燃料替代与稳定供电。','数据中心：微网与UPS、备用体系协调，连续供电优先。','乡村：并网消纳与偏远独立供电并存，强调简便运维。'],'定性架构框图。无数值轴；横向五类场景，纵向客户需求、配置、付费价值。蓝色并网，绿色独立/弱网，橙色两类均适用；不使用饼图虚构份额。','五幅等宽写实小景横排：光伏工厂、海岛村落、露天矿区、数据中心、乡村设施。统一斜俯视与晴天光照，按场景配置储能；海岛矿区增加备用机组。蓝绿与自然灰。')

# 07 — Competition
s=base(7,'市场竞争格局：设备、集成与软件三层交叉','最终竞争指向可验证的系统性能、交付责任与全生命周期服务',section='01 / COMPETITIVE LANDSCAPE')
rows=[('软件与控制平台','EMS / 预测优化 / 持续运维','授权与服务收入','施耐德 · 西门子 · 安科瑞',TEAL),('系统集成商','设计 / 保护控制 / 联调交付','工程交付收入','中国电建旗下工程企业等',BLUE),('设备供应商','逆变器 / 储能 / 配电设备','设备销售收入','阳光电源等',ORANGE)]
for i,(title,ability,rev,examples,c) in enumerate(rows):
    y=2.25+i*1.24;rect(s,.65,y,9.1,1.08,WHITE,radius=True);rect(s,.65,y,.07,1.08,c)
    text(s,.87,y+.2,2.35,.38,title,18,INK,True);text(s,3.25,y+.17,3.55,.35,ability,13,GRAY)
    text(s,3.25,y+.62,5.9,.3,'代表：'+examples,11,c)
    text(s,7.05,y+.2,2.4,.32,rev,13,INK,True)
    line(s,9.75,y+.54,10.18,y+.54,c,1.7)
rect(s,10.18,2.25,2.5,3.56,NAVY,radius=True);text(s,10.4,2.62,2.05,.45,'终端业主',22,WHITE,True,'center')
text(s,10.43,3.42,1.96,1.9,'性能验收\n收益核验\n责任边界\n持续服务',16,'BED2DE',False,'center')
footer(s,'代表企业仅作业务示例，不表示排名或市场份额；企业可跨层布局。产品与案例来源详见各页备注。')
note(s,'市场竞争格局：玩家分层（设备商、集成商、软件平台）',['设备商围绕性能、安全与成本竞争。','集成商围绕系统责任、保护控制与交付经验竞争。','软件平台围绕EMS、预测调度、设备接入和运营服务竞争。','企业可跨层布局；最终竞争是系统能力和持续服务。'],'定性架构框图；无数值坐标。设备、集成、软件三层连接终端业主；绿/蓝/橙区分层次。比较交付物、客户接口、收入方式、壁垒。企业仅为示例，无排名或份额含义。','三层透明剖面工业场景：底层逆变器储能开关柜，中层工程联调，上层能源调度台，右侧业主接收服务。银灰设备，蓝绿数据线；不使用Logo。',[SOURCES['sungrow'],SOURCES['epc'],SOURCES['ems'],SOURCES['siemens'],SOURCES['acrel']])

# 08 — PEST
s=base(8,'PEST分析：政策支持明确，商业兑现依赖地方条件','外部环境决定需求方向，项目条件决定可实现收益',section='01 / EXTERNAL ENVIRONMENT')
items=[('P','政策','主配微协同、就近消纳','接网、交易与责任边界',BLUE),('E','经济','设备降本扩大可行空间','价差、利用小时与融资成本',TEAL),('S','社会','连续供电、绿色采购需求','支付能力与专业运维资源',TEAL),('T','技术','构网、储能、数字化能力','互操作与系统验证',BLUE)]
for i,(ch,title,driver,risk,c) in enumerate(items):
    x=.65+(i%2)*6.1;y=2.2+(i//2)*2.0
    rect(s,x,y,5.92,1.8,WHITE,radius=True);text(s,x+.22,y+.2,.65,.65,ch,32,c,True)
    text(s,x+1.02,y+.23,4.5,.4,title,20,INK,True)
    text(s,x+1.03,y+.85,4.53,.31,'驱动  '+driver,13,TEAL)
    text(s,x+1.03,y+1.3,4.53,.32,'约束  '+risk,13,RED)
footer(s,'PEST为定性分析；政策依据：国家发展改革委、国家能源局《关于促进电网高质量发展的指导意见》。')
note(s,'PEST分析：行业外部环境',['P：支持智能微网、就近消纳，接网交易责任需逐项目落实。','E：降本扩大空间，价差、利用小时及融资决定回报。','S：连续供电、绿色采购与能源可及性拉动需求。','T：构网与数字化增强能力，跨厂商协同是落地重点。'],'定性PEST四象限图，无数值坐标。绿色代表驱动，红橙色代表约束。每象限呈现外部变化及项目影响，不制作伪量化分数。','四幅局部照片围绕微网图标：政策文件与电网、工业电表与账单、园区人员、储能实验室。深蓝线框分隔、浅灰底、绿橙点缀，避免过多符号。',[SOURCES['policy']])

# 09 — Architecture
s=base(9,'微电网系统架构拆解：源网荷储协同，控制分层闭环','快速稳定由设备与保护保障；微网控制器协调运行；EMS优化计划和经济性',section='02 / SYSTEM ARCHITECTURE')
rect(s,.65,2.18,9.05,4.12,WHITE,radius=True)
node(s,3.71,2.36,2.65,.76,'公共电网','',BLUE);line(s,5.03,3.12,5.03,3.91,BLUE,2)
badge(s,5.23,3.33,1.3,'PCC / 保护',RED,'F8EEEB')
line(s,1.22,3.92,9.12,3.92,BLUE,4);text(s,1.23,3.58,2.2,.26,'交流母线 / 电气边界',10,GRAY)
for x,title,sub in [(1.0,'源','风电 / 光伏'),(3.1,'储','电池 + PCS'),(5.2,'荷','关键 / 可调负荷'),(7.3,'V2G','双向车桩')]:
    line(s,x+.9,3.92,x+.9,4.48,TEAL,2);node(s,x,4.48,1.8,1.1,title,sub)
text(s,1.05,5.88,8.2,.25,'独立型场景：取消公共电网支路，配置本地构网来源与备用能力',11,TEAL,True)
node(s,10.0,2.23,2.67,1.02,'EMS','预测 / 计划 / 经济优化',TEAL)
node(s,10.0,3.72,2.67,1.02,'微网控制器','功率协调 / 运行模式',TEAL)
node(s,10.0,5.21,2.67,1.02,'设备控制与保护','快速响应 / 独立安全链',RED)
line(s,11.33,3.25,11.33,3.72,TEAL,1.5,True);line(s,11.33,4.74,11.33,5.21,TEAL,1.5,True)
line(s,9.1,5.02,9.82,5.02,TEAL,1.2,True);line(s,9.82,5.02,9.82,5.72,TEAL,1.2,True);line(s,9.82,5.72,10,5.72,TEAL,1.2,True)
footer(s,'图例：蓝色粗线＝电力母线；绿色实线＝设备电力连接；绿色虚线＝控制通信；红色标记＝保护与安全。')
note(s,'微电网系统架构拆解图（源网荷储）',['源：风光与必要的可调电源。','网：PCC、母线、保护与计量界定边界。','荷储：关键负荷优先，可调负荷和储能提供灵活性。','控制：设备控制、微网控制器、EMS分层闭环。'],'定性架构框图，无数值坐标。中心交流母线连接风光、储能、负荷和V2G；上接公共电网及PCC保护。右侧EMS、微网控制器、设备控制与保护。实线电力、虚线通信；储能/车桩支持双向功率。独立型取消公共电网支路。','白底工程信息图，风机、光伏、厂房、储能和车桩等距图标围绕母线，控制中心在顶部。深蓝电力线、青绿通信线、橙红保护，标签后期添加。')

# 10 — Stack roadmap
s=base(10,'当前主流技术栈盘点：成熟设备与分层控制构成交付基础','储能时长、控制方式与移动储能接入，均需按场景确定',section='02 / TECHNOLOGY STACK')
cols=[('成熟应用',3.35),('加速推广',6.43),('场景验证',9.51)]
for lab,x in cols:badge(s,x,2.22,2.75,lab,TEAL,PALE)
labels=['能源与储能','电力电子 / 保护','管理与通信','移动储能']
cells=[['风光 / 磷酸铁锂 / 备用','配置优化与标准化交付','长时储能场景适配'],['PCS / 保护 / 同期并网','复杂场景构网 / 多机协同','高比例电力电子整网验证'],['SCADA / 规则型EMS','预测优化 / 孪生辅助','高自治AI / 跨微网协同'],['有序充电 / 负荷管理','车队双向充放电试点','广泛V2G聚合与结算']]
for i,lab in enumerate(labels):
    y=2.85+i*.8;text(s,.75,y+.14,2.5,.4,lab,16,INK,True)
    for j,(_,x) in enumerate(cols):
        rect(s,x,y,2.75,.65,WHITE,LINE,radius=True);text(s,x+.12,y+.16,2.5,.4,cells[i][j],11.3,GRAY,False,'center')
rect(s,.75,6.22,11.8,.28,PALE);text(s,.85,6.24,11.6,.23,'V2G前提：车辆兼容 · 停车时段 · 用户授权 · 出行电量保障 · 结算机制',10.5,TEAL,True,'center')
footer(s,'成熟度为本稿定性判断，不代表渗透率。国内车网互动规模化应用已有试点，来源详见备注。')
note(s,'当前主流技术栈盘点',['能源层：风光、磷酸铁锂储能、备用；储能时长由需求决定。','电力电子与保护层：PCS、跟网/构网、同期并网及故障隔离。','管理通信层：EMS、SCADA、预测优化、标准接口及网络安全。','V2G需兼容、授权、出行保障与结算条件。'],'定性技术路线图。横向成熟应用、加速推广、场景验证；纵向四个技术层。矩阵列出代表技术，属于分析判断，非渗透率数据。','浅灰工业机房内横排逆变器、液冷储能、保护装置、边缘控制器和双向充电桩。统一比例，蓝绿指示灯，少量橙色线缆，上方留路线图空间。',[SOURCES['v2g']])

# 11 — GFM
s=base(11,'核心技术趋势1：构网型逆变器成为刚需','首先发生在孤岛与弱网场景；系统必须有构网来源，不等于所有逆变器都必须构网',section='02 / GRID-FORMING',dark=True)
for i,(title,sub) in enumerate([('强网并网','外部电网提供稳定参考'),('弱网运行','本地支撑与协同能力增强'),('高比例逆变器孤岛','本地构网来源不可缺少')]):
    x=.7+i*4.12;node(s,x,2.3,3.87,1.15,title,sub,LIME,True)
text(s,.75,3.95,5.65,.48,'跟网型：跟随外部电压参考',21,WHITE,True)
text(s,.75,4.65,5.48,1.07,'构网型：主动建立电压参考\n参与频率支撑与功率分担',19,LIME,True)
rect(s,7.08,3.92,5.57,2.3,DARKCARD,radius=True)
text(s,7.36,4.16,4.98,.4,'采购与验收看什么？',20,WHITE,True)
text(s,7.36,4.83,4.96,1.02,'弱网稳定 · 故障限流 · 多机协同\n并离网切换 · 黑启动系统条件',16,'BDD0DC')
footer(s,'来源：NREL构网路线图。同步机亦可提供构网来源；黑启动还取决于储能状态、辅助电源及系统配置。')
note(s,'核心技术趋势1：构网型逆变器成为刚需',['新能源与电力电子占比上升，系统需要稳定电压频率参考。','跟网型依赖外部参考；构网型主动建立参考并参与功率分担。','孤岛必须有构网来源：同步机或构网逆变器。','验收弱网稳定、切换、限流、多机协同及黑启动系统条件。'],'定性技术路线图。横向强网并网、弱网运行、高比例逆变器孤岛，呈现能力需求演进；无数量坐标。绿色强调本地构网能力，不能由此推导市场渗透率。不绘制无实测依据的频率响应曲线。','近景储能PCS和电池箱，中景工厂母线与分区负荷，远景公共电网。克制的绿色连接线表示本地支撑，深蓝夜景、橙色状态灯，强调连续供电，不使用能量护盾等失真表现。',[SOURCES['gfm']])

# 12 — AI
s=base(12,'核心技术趋势2：AI+EMS、数字孪生、多微网协同','预测更准确、决策有约束、结果可回测；快速保护与控制保持本地自治',section='02 / INTELLIGENT OPERATIONS')
steps=[('采集','设备 / 天气 / 电价'),('预测','风光 / 负荷 / 价格'),('孪生校验','模型 / 状态 / 策略'),('优化','功率 / SOC / 出行'),('执行反馈','边缘执行 / 回测')]
for i,(a,b) in enumerate(steps):
    x=.7+i*2.43;node(s,x,2.4,2.23,1.22,a,b,TEAL)
    if i<4:line(s,x+2.23,3.0,x+2.43,3.0,TEAL,1.8)
line(s,11.74,3.62,11.74,4.02,TEAL,1.3,True);line(s,1.81,4.02,11.74,4.02,TEAL,1.3,True);line(s,1.81,4.02,1.81,3.62,TEAL,1.3,True)
for i,(title,body) in enumerate([('AI + EMS','改进预测与约束优化\n以实际运行结果检验收益'),('数字孪生 / 多微网','策略预演、模型校准\n协同受线路与交易规则约束'),('V2G柔性资源','按在线率与离站需求调度\n电池容量不等于可用容量')]):
    x=.7+i*4.1;rect(s,x,4.38,3.89,1.75,WHITE,radius=True);text(s,x+.18,4.59,3.53,.4,title,18,INK,True);text(s,x+.18,5.2,3.53,.68,body,13,GRAY)
footer(s,'验证指标：预测误差、约束违例次数、单位供电成本、关键负荷保障时长。AI预测优化商业产品来源详见备注。')
note(s,'核心技术趋势2：AI+EMS、数字孪生、多微网协同调度',['AI改进预测并在安全约束内优化。','数字孪生关联设备网络模型与实时数据，支持预演诊断校准。','多微网局部自治、协调功率与备用；互济受线路和交易规则约束。','V2G调度考虑车辆在线、离站电量和损耗，不把全容量视为可用。'],'定性闭环架构图，无数值坐标。采集→预测→孪生校验→约束优化→执行反馈；虚线反馈闭环。维度包括输入、模型、决策、约束和验证。快速保护与控制本地自治，不依赖云端优化。','左侧真实园区，右侧对应半透明数字模型，设备位置对应；下方多个园区与物流车连接协同平台。深蓝底、青绿线框、橙色异常标记，界面简洁，避免虚构读数。',[SOURCES['ems']])

# 13 — Economics
s=base(13,'行业痛点与商业化瓶颈：技术可行，未必形成稳定现金流','收益波动、交付复杂、持续运营能力，决定项目能否从示范走向复制',section='03 / COMMERCIALIZATION')
native_line(s,.8,2.65,7.65,3.45,['0.45','0.65','0.85'],[('套利毛贡献',[44.4,66,87.6],BLUE),('扣运维后净贡献',[29.4,51,72.6],TEAL)],100,20,'年度现金贡献 / 万元')
text(s,2.55,6.08,4.4,.3,'峰谷价差 / 元每千瓦时',11,GRAY,False,'center')
rect(s,8.76,2.2,3.88,4.03,WHITE,radius=True)
text(s,9,2.45,3.4,.4,'仅靠套利，回报敏感',19,INK,True)
text(s,9,3.15,3.39,1.42,'4MWh储能 · 投资500万元\n年放电108万kWh\n往返效率90%\n年度运维15万元',13,GRAY)
line(s,9,4.78,12.36,4.78,LINE)
text(s,9,5.01,3.35,.36,'简单回收期：17.0 → 6.9年',15,TEAL,True)
text(s,9,5.58,3.35,.4,'对应价差0.45 → 0.85元/kWh',11,GRAY)
footer(s,'本稿示例测算：谷价固定0.35元/kWh。未计税费、融资、衰减及更换；不含光伏、保供和其他服务收益。')
note(s,'行业痛点与商业化瓶颈',['收益受价差、循环次数和消纳影响；收益叠加避免重复占用同一调节能力。','跨厂商接入、保护整定、并离网联调与责任边界增加交付成本。','衰减、运维、网络安全和客户信用影响长期运行。','储能仅靠峰谷套利时对价差敏感，应评估完整微网价值。'],'定量敏感性折线图。横轴峰谷价差0.45/0.65/0.85元每千瓦时；纵轴年现金贡献（万元，0起）。4MWh，投资500万元，年放电108万kWh，往返效率90%，谷价0.35，运维15万元。毛贡献44.4/66/87.6；净贡献29.4/51/72.6；简单回收17.0/9.8/6.9年。公式：放电量×峰价－放电量÷效率×谷价－运维。未计税融资衰减更换；无光伏或其他收益。蓝毛贡献、绿净贡献。','左侧运行储能站，右侧工程师与业主查看收益曲线和状态。冷灰深蓝，橙色强调关注点；人物自然、设备真实，预留浅色图表区域。')

# 14 — Roadmap
s=base(14,'未来3—5年市场机会与投资方向','先验证可付费场景与交付能力，再扩展协同平台和持续服务',section='03 / OPPORTUNITIES')
years=['2027','2028','2029','2030','2031'];x0=3.45;cw=1.8
for i,yr in enumerate(years):text(s,x0+i*cw,2.2,cw,.35,yr,15,GRAY,True,'center')
lanes=[('场景交付','园区 / 海岛 / 矿区',0,2,BLUE),('核心设备','构网PCS / 保护协同',1,2,TEAL),('软件运营','EMS改造 / 数字孪生',1,4,TEAL),('移动与协同','车队V2G / 多微网',2,3,ORANGE)]
for i,(name,detail,start,length,c) in enumerate(lanes):
    y=2.84+i*.74;text(s,.78,y+.02,2.4,.3,name,17,INK,True);text(s,.78,y+.37,2.55,.25,detail,10,GRAY)
    line(s,x0,y+.3,12.45,y+.3,LINE,1)
    rect(s,x0+start*cw,y+.06,length*cw-.1,.47,c,radius=True)
    text(s,x0+start*cw+.1,y+.14,length*cw-.3,.3,'优先投入' if i<2 else '按验证结果逐步扩张',11,WHITE,True,'center')
rect(s,.78,6.08,11.68,.36,PALE,radius=True);text(s,.9,6.14,11.4,.25,'投资筛选：负荷数据可得  /  验收案例可信  /  运维能力可持续  /  收益结算可完成',11,TEAL,True,'center')
footer(s,'路线图为战略建议，非普及率或收益预测。阶段验收：首批项目 → 跨项目复制 → 持续服务收入。')
note(s,'未来3-5年市场机会与投资方向',['2027—2028优先标准化园区及海外海岛矿区，围绕降本或燃料替代。','2028—2029升级构网PCS、保护协同、存量EMS与验证服务。','2029—2031视条件扩张多微网、孪生运营、车队V2G。','投资优先负荷数据、验收案例、持续运维与结算能力。'],'定性技术路线图。横轴2027—2031，纵向场景交付、核心设备、软件运营、移动与协同四赛道。蓝/绿/橙区分赛道；条带代表战略投入窗口，不代表市场规模。验证节点为首批验收、跨项目复制、持续收入。','连续地平线的三段场景：单园区交付、多园区复制、跨园区调度和车队接入。蓝绿为主、橙色节点，场景逐步扩展，不科幻，上方预留路线图。')

# 15 — Conclusions
s=base(15,'总结与核心判断：系统能力与可验证收益决定价值','把趋势判断转化为场景、能力、收益和复制条件四项决策',section='03 / STRATEGIC TAKEAWAYS',dark=True)
for i,(n,t,b,c) in enumerate([('01','选场景','并网：降本与互动\n独立：保供与燃料替代',BLUE),('02','配能力','构网保障稳定\nEMS提升经济性',TEAL),('03','验收益','明确运行基线\n核验全生命周期现金流',ORANGE),('04','做复制','标准化交付\n持续运维与责任闭环',LIME)]):
    x=.7+i*3.08;card(s,x,2.28,2.88,3.5,n,t,b,True,c)
text(s,.78,6.12,11.8,.36,'行动顺序：明确客户需求 → 建立运行基线 → 完成技术与收益验收 → 批量复制',14,LIME,True,'center')
footer(s,'市场口径分别评估，技术能力按工况验证，商业价值以可核验运行数据和结算结果为依据。')
note(s,'总结与核心判断',['全球扩张与中国需求并行，全口径与新能源项目空间分别评估。','构网保障稳定，EMS提升经济性，孪生和协同扩展运营价值。','并网验证降本互动，独立验证保供燃料替代。','选择场景、建立基线、验收能力收益、再复制。'],'定性架构框图，无数值轴。四模块选场景→配能力→验收益→做复制；维度为场景适配、性能边界、收益证据、复制条件。蓝需求、绿技术、橙经济、浅绿交付。','广角现代工业园区，光伏、储能、充电、生产建筑协调，前景两位工程师查看简洁看板。晨光、浅蓝天空、青绿植被，左上留四条判断区域。')

# 16 — Q&A
s=base(16,'','',section='DISCUSSION  /  NEXT STEP',dark=True)
text(s,.72,1.53,5.9,1.4,'Q&A',76,WHITE,True)
text(s,.79,3.21,5.8,1.25,'把行业趋势转化为\n具体项目决策',28,LIME,True)
text(s,.8,5.13,5.3,.7,'下一步所需资料\n负荷曲线 · 接网条件 · 场地资源 · 结算机制',14,'B5CCD9')
qs=[('需求','电费、绿电还是连续供电？'),('技术','是否孤岛？关键负荷保多久？'),('商务','设备采购、总包还是运营？'),('实施','数据、资源、结算是否具备？')]
for i,(a,b) in enumerate(qs):
    y=1.72+i*1.12;rect(s,7.1,y,5.5,.93,DARKCARD,radius=True)
    text(s,7.33,y+.23,.86,.4,a,17,LIME,True);text(s,8.46,y+.26,3.85,.42,b,14,WHITE)
note(s,'Q&A',['场景：电费、绿电还是连续供电？','技术：是否孤岛，保障多久？','商务：采购、工程总包还是能源服务？','实施：负荷曲线、接网、场地和结算是否具备？'],'定性讨论架构，无数值坐标。需求、技术、商务、实施四节点；围绕项目可行性展开，不引入新市场数据。','深蓝渐变，底部细线园区轮廓含风机、光伏、储能、工厂、车辆，青绿色线连接。中央大留白呈现Q&A，简洁安静，与封面呼应。')

# Save editable presentation and source manuscript
target=OUT/'新能源微电网_市场洞察与技术趋势分析_16页.pptx'
prs.save(target)
(OUT/'逐页文稿_图表口径与配图描述.md').write_text('\n\n---\n\n'.join(f'【第{i+1}页】\n{n}' for i,n in enumerate(notes)),encoding='utf-8')

# Independent layout proof, built from the same text and geometry; not a PowerPoint renderer.
SCALE=120
def px(n):return round(n*SCALE)
def font(sz,bold=False):return ImageFont.truetype(FB if bold else FP,round(sz*SCALE/72))
def wrapped(t,f,maxw,d):
    out=[]
    for para in t.split('\n'):
        cur=''
        for ch in para:
            if cur and d.textlength(cur+ch,font=f)>maxw:out.append(cur);cur=ch
            else:cur+=ch
        out.append(cur)
    return out
for idx,s in enumerate(slides):
    im=Image.new('RGB',(1600,900),'white');d=ImageDraw.Draw(im)
    for el in s._draw:
        kind=el[0]
        if kind=='bg':d.rectangle((0,0,1600,900),fill='#'+el[1])
        elif kind=='rect':
            _,x,y,w,h,c,lc,rad=el;box=(px(x),px(y),px(x+w),px(y+h))
            if rad:d.rounded_rectangle(box,radius=9,fill='#'+c,outline='#'+lc if lc else None,width=1)
            else:d.rectangle(box,fill='#'+c,outline='#'+lc if lc else None,width=1)
        elif kind=='line':
            _,x1,y1,x2,y2,c,ww,dash=el
            if dash:
                dist=math.hypot(x2-x1,y2-y1);n=max(1,int(dist*12))
                for k in range(0,n,2):
                    a=k/n;b=min((k+1)/n,1);d.line((px(x1+(x2-x1)*a),px(y1+(y2-y1)*a),px(x1+(x2-x1)*b),px(y1+(y2-y1)*b)),fill='#'+c,width=max(1,round(ww*SCALE/72)))
            else:d.line((px(x1),px(y1),px(x2),px(y2)),fill='#'+c,width=max(1,round(ww*SCALE/72)))
        elif kind=='text':
            _,x,y,w,h,t,sz,c,b,align=el;f=font(sz,b);ls=wrapped(t,f,px(w),d);lh=round(sz*SCALE/72*1.22)
            if len(ls)*lh>px(h)+8 and t:warnings.append({'slide':idx+1,'text':t,'height':h,'required':round(len(ls)*lh/SCALE,2)})
            yy=px(y)
            for st in ls:
                tw=d.textlength(st,font=f);xx=px(x)+(0 if align=='left' else (px(w)-tw)/2 if align=='center' else px(w)-tw)
                d.text((xx,yy),st,font=f,fill='#'+c,anchor='lt');yy+=lh
        elif kind=='chart':
            _,x,y,w,h,cats,sers,mx,step,unit,dark=el
            l=px(x+.47);r=px(x+w-.15);top=px(y+.08);bot=px(y+h-.68)
            fg='B5CBD8' if dark else GRAY;grid='2C485F' if dark else LINE
            f=font(11)
            for v in range(0,mx+1,step):
                yy=bot-(bot-top)*v/mx;d.line((l,yy,r,yy),fill='#'+grid,width=1);d.text((l-9,yy),str(v),font=f,fill='#'+fg,anchor='rm')
            xpos=[l+(r-l)*i/(len(cats)-1) for i in range(len(cats))]
            for xp,lab in zip(xpos,cats):d.text((xp,bot+14),lab,font=f,fill='#'+fg,anchor='mt')
            for si,(name,vals,c) in enumerate(sers):
                points=[(xp,bot-(bot-top)*v/mx) for xp,v in zip(xpos,vals)]
                d.line(points,fill='#'+c,width=4)
                for xp,yp in points:d.ellipse((xp-5,yp-5,xp+5,yp+5),fill='#'+c)
                if len(sers)==1:
                    for (xp,yp),v in zip(points,vals):d.text((xp,yp-13),str(v),font=font(10,True),fill='#'+c,anchor='mb')
                lx=l+si*(r-l)/max(1,len(sers));ly=px(y+h-.18);d.line((lx,ly,lx+24,ly),fill='#'+c,width=4);d.text((lx+32,ly),name,font=font(10),fill='#'+fg,anchor='lm')
    im.save(OUT/f'preview_{idx+1:02}.png');previews.append(im)
thumb=Image.new('RGB',(1600,1000),'#D9E4EB');td=ImageDraw.Draw(thumb)
for i,im in enumerate(previews):
    tile=im.resize((384,216));xx=16+(i%4)*400;yy=16+(i//4)*246;thumb.paste(tile,(xx,yy));td.text((xx,yy+219),f'{i+1:02d}',font=font(10,True),fill='#'+INK)
thumb.save(OUT/'16页总览.png')
previews[0].save(OUT/'新能源微电网_版式预览.pdf',save_all=True,append_images=previews[1:],resolution=120.0)
(OUT/'layout_checks.json').write_text(json.dumps(warnings,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pptx':str(target),'slides':len(prs.slides),'charts':sum(1 for s in prs.slides for sh in s.shapes if sh.has_chart),'notes':len(notes),'layout_warnings':warnings},ensure_ascii=False,indent=2))
