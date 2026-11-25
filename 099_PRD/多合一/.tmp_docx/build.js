const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  TableOfContents, PageNumber, Header, Footer, LevelFormat,
  VerticalAlign, PageBreak, LineRuleType, convertInchesToTwip
} = require("docx");

const SONG = { eastAsia: "宋体", ascii: "Times New Roman", hAnsi: "Times New Roman" };
const HEI = { eastAsia: "黑体", ascii: "Arial", hAnsi: "Arial" };
const INK = "1A1A1A";
const NAVY = "1F3864";
const GREY = "595959";
const HDR_FILL = "E9EEF7";

const CONTENT_W = 9026;

function R(text, o) {
  o = o || {};
  return new TextRun({
    text: text,
    font: o.hei ? HEI : SONG,
    size: o.size || 21,
    bold: !!o.bold,
    color: o.color || INK,
    italics: !!o.italics
  });
}

function P(text, o) {
  o = o || {};
  return new Paragraph({
    children: [R(text, o)],
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: o.spacing || { line: 340, lineRule: LineRuleType.AUTO, before: 0, after: 120 },
    indent: o.indent,
    keepNext: !!o.keepNext,
    pageBreakBefore: !!o.newPage
  });
}

function H1(text, o) {
  o = o || {};
  return new Paragraph({ text: text, heading: HeadingLevel.HEADING_1, pageBreakBefore: !!o.newPage });
}

function H2(text) {
  return new Paragraph({ text: text, heading: HeadingLevel.HEADING_2 });
}

function H3(text) {
  return new Paragraph({ text: text, heading: HeadingLevel.HEADING_3 });
}

function BULLET(text) {
  return new Paragraph({
    numbering: { reference: "dot-bullet", level: 0 },
    children: [R(text)],
    spacing: { line: 320, lineRule: LineRuleType.AUTO, before: 0, after: 80 }
  });
}

function CAPTION(text) {
  return new Paragraph({
    children: [R(text, { size: 19, bold: true, color: "404040" })],
    spacing: { before: 160, after: 80, line: 280, lineRule: LineRuleType.AUTO },
    keepNext: true
  });
}

function NOTE(text) {
  return new Paragraph({
    children: [R(text, { size: 18, color: GREY })],
    spacing: { before: 60, after: 160, line: 280, lineRule: LineRuleType.AUTO }
  });
}

function cellPara(text, o) {
  o = o || {};
  return new Paragraph({
    children: [R(text, { size: 19, bold: !!o.bold, color: o.color || INK, hei: !!o.bold })],
    alignment: o.align || AlignmentType.LEFT,
    spacing: { line: 260, lineRule: LineRuleType.AUTO, before: 20, after: 20 },
    keepNext: !!o.keepNext
  });
}

function cell(text, width, o) {
  o = o || {};
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    shading: o.fill ? { type: ShadingType.CLEAR, color: "auto", fill: o.fill } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    children: [cellPara(text, o)]
  });
}

function makeTable(widths, header, rows, o) {
  o = o || {};
  const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
  const borders = { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border };
  const total = widths.reduce(function (a, b) { return a + b; }, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: header.map(function (t, i) {
      return cell(t, widths[i], { bold: true, fill: HDR_FILL, align: AlignmentType.CENTER, color: NAVY });
    })
  });
  const bodyRows = rows.map(function (r, ri) {
    const keep = !!o.keepTogether && ri < rows.length - 1;
    return new TableRow({
      cantSplit: true,
      children: r.map(function (t, i) {
        return cell(t, widths[i], { keepNext: keep, align: i === 0 && !o.centerFirst ? AlignmentType.LEFT : (o.centerFirst ? AlignmentType.CENTER : AlignmentType.LEFT) });
      })
    });
  });
  return new Table({
    columnWidths: widths,
    width: { size: total, type: WidthType.DXA },
    borders: borders,
    rows: [headerRow].concat(bodyRows)
  });
}

const children = [];

children.push(new Paragraph({
  children: [R("澜潮科技 · SKU2 双鉴存在传感器", { size: 19, color: GREY })],
  spacing: { before: 240, after: 60, line: 280, lineRule: LineRuleType.AUTO }
}));

children.push(new Paragraph({
  children: [R("PIR 与毫米波雷达模组关键参数解读", { size: 40, bold: true, color: NAVY, hei: true })],
  spacing: { before: 120, after: 80, line: 400, lineRule: LineRuleType.AUTO }
}));

children.push(new Paragraph({
  children: [R("挂壁安装场景：安装高度、检测范围与识别精度", { size: 24, color: "2F5496" })],
  spacing: { before: 0, after: 120, line: 320, lineRule: LineRuleType.AUTO },
  border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: "2F5496", space: 8 } }
}));

children.push(new Paragraph({ children: [R("")], spacing: { before: 0, after: 120, line: 200, lineRule: LineRuleType.AUTO } }));

children.push(makeTable(
  [1500, 3163, 1500, 2863],
  ["项目", "内容", "项目", "内容"],
  [
    ["文档版本", "V1.0", "编制日期", "2026-11-25"],
    ["适用产品", "SKU2 双鉴存在传感器", "覆盖形态", "侧装（挂壁）"],
    ["资料来源", "D210AX、E54-24LD12A 规格书", "数据状态", "原始值，未二次标定"],
    ["文档用途", "挂壁安装的选型与布点依据", "待办事项", "见附录 B 待实测项"]
  ]
));

children.push(new Paragraph({ children: [R("")], spacing: { before: 0, after: 60, line: 200, lineRule: LineRuleType.AUTO } }));

children.push(new Paragraph({
  children: [R("目录", { size: 28, bold: true, color: NAVY, hei: true })],
  spacing: { before: 240, after: 120, line: 320, lineRule: LineRuleType.AUTO }
}));

children.push(new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-2" }));

children.push(P("本文依据两份供应商规格书，梳理 SKU2 在挂壁安装形态下的安装高度、检测范围与识别精度。两份文档的层级并不相同，这一点决定了参数的读法，因此在进入正题之前先作区分：", { newPage: true, spacing: { line: 340, lineRule: LineRuleType.AUTO, before: 120, after: 120 } }));

children.push(BULLET("D210AX 是裸热释电元件，内部集成 16 位 ADC、抽取滤波与单线串行接口，输出的是红外差分能量的原始波形，不含菲涅尔透镜，因此规格书中没有安装高度与探测距离。"));
children.push(BULLET("E54-24LD12A 是成品模组，内部集成 24GHz FMCW 收发、天线与 MCU 算法，直接输出有人无人状态与目标距离，因此挂壁安装的高度与范围有明确标称值。"));

children.push(P("换言之，PIR 章节回答的是“器件能感知到什么角度的热变化”，雷达章节回答的是“整机在墙上能覆盖多大空间”。两者不可直接比较，但可以互补。", { spacing: { line: 340, lineRule: LineRuleType.AUTO, before: 60, after: 160 } }));

children.push(H1("第一章  PIR 传感器（D210AX）"));

children.push(H2("1.1  器件定位"));
children.push(P("D210AX 由苏州英瑞传感技术有限公司（ENRAY）生产，是一款数字输出的双元热释电红外传感器。与传统的三脚模拟 PIR 不同，它把敏感元、ADC、数字滤波和串行接口封装在同一个金属外壳内，主控通过一根 DOCI 线即可读出 16 位数据，无需外部运放与比较器。"));
children.push(P("这一定位带来两个直接后果：一是功耗极低，工作电流仅 6 µA，适合微能量取电产品；二是输出的是波形而非开关量，触发判决完全由主控固件负责，探测距离、延时、灵敏度都必须由整机定义。"));

children.push(H2("1.2  关键参数"));

children.push(CAPTION("表 1-1  D210AX 电气与光学参数"));
children.push(makeTable(
  [1900, 2900, 4226],
  ["参数", "数值", "条件与说明"],
  [
    ["工作电压", "2.4 / 3.0 / 3.6 V", "最小值 / 典型值 / 最大值"],
    ["工作电流", "6 µA", "VDD = 3.0 V，不带负载"],
    ["工作温度", "-40 ~ 85 ℃", "存储温度同为 -40 ~ 85 ℃"],
    ["内部振荡频率", "44.8 / 64 / 83.2 kHz", "内部时钟为 FOSC / 2"],
    ["DOCI 驱动能力", "拉高 200 µA；拉低 130 µA", "数据引脚双向驱动"],
    ["输入电平", "VIL ≤ 20% VDD；VIH ≥ 80% VDD", "主控 IO 判决门限"],
    ["滤光片起通波长", "5000 ± 400 nm", "5% 透过点"],
    ["带内平均透过率", "7 ~ 14 µm ≥ 70%", "人体红外主波段"],
    ["带外平均透过率", "400 ~ 4500 nm ≤ 0.5%", "可见光与近红外截止"]
  ]
));

children.push(CAPTION("表 1-2  D210AX 传感器性能"));
children.push(makeTable(
  [1900, 2900, 4226],
  ["参数", "数值", "条件与说明"],
  [
    ["ADC 精度", "16 bit", "片内集成"],
    ["ADC 分辨率", "1.5 µV / count", "决定最小可辨信号台阶"],
    ["噪声", "40 count", "约合 60 µV 等效输入噪声"],
    ["感度", "900 / 1200 / 1800 count", "最小值 / 典型值 / 最大值"],
    ["平衡感度比", "25%", "双敏感元一致性"],
    ["频率响应", "0.4 ~ 7.0 Hz 显著", "峰值约 0.3 ~ 1 Hz，峰值响应度约 20 kV/W"],
    ["视角（X 轴）", "138°", "元件级接收角"],
    ["视角（Y 轴）", "125°", "元件级接收角"]
  ]
));

children.push(H2("1.3  视角与结构"));
children.push(P("规格书给出的视野角为 X 轴 138°、Y 轴 125°，这是敏感元本身的光学接收角，不是整机探测角。加装菲涅尔透镜后，有效视场会被透镜的分区结构重新切割，通常收窄到 90° ~ 120°，并形成若干交替的明暗扇区，人体穿越扇区时才会产生可识别的差分信号。"));
children.push(P("结构上，外壳直径 Ø8.2 ± 0.1 mm，本体高度 3.8 ± 0.2 mm（含帽 4.55 ± 0.2 mm），滤光窗口 4 ± 0.2 mm 见方，三根引脚 Ø0.45 mm、长 13.5 ± 1 mm。内部为两个 1 × 1 mm 的敏感元，中心间距 2.3 mm，采用差分配置以抵消环境温度的缓慢漂移。"));

children.push(H2("1.4  数据输出"));
children.push(P("DOCI 是单线双向引脚。平时为低电平，数据就绪时输出高电平引导脉冲，主控检测到后把 IO 切为输出并拉低，随后逐位读出 25 bit。每一位都需要主控先输出低电平、再输出高电平，然后把 IO 切回输入读取电平，低为 0、高为 1。"));

children.push(CAPTION("表 1-3  DOCI 读时序"));
children.push(makeTable(
  [2400, 2200, 2200, 2226],
  ["符号", "最小", "典型", "最大"],
  [
    ["T 引导", "45 µs", "50 µs", "200 µs"],
    ["T 低电平", "0.8 µs", "1 µs", "4 µs"],
    ["T 高电平", "0.8 µs", "1 µs", "4 µs"],
    ["T 判断", "5 µs", "10 µs", "20 µs"]
  ],
  { keepTogether: true }
));

children.push(P("25 bit 中，Bit24 为符号位，Bit24 ~ Bit9 共 16 位构成有效 PIR 数据。为得到连贯波形，需要按下述规则换算：读数大于 32767 时减去 32768，小于等于 32767 时加上 32768。规格书特别提示，每一笔数据都必须读取，跳读会导致后续数据异常波动。", { spacing: { line: 340, lineRule: LineRuleType.AUTO, before: 120, after: 120 } }));

children.push(H2("1.5  挂壁安装要点"));
children.push(BULLET("规格书未给出安装高度与探测距离，两者需由实装透镜和固件门限确定，必须以整机实测数据为准。"));
children.push(BULLET("透镜光轴建议水平或下倾 10° ~ 15°，下倾过大会压缩远端覆盖，过大仰角则把视场抬向天花板。"));
children.push(BULLET("避开空调出风口 1.5 m 以上、新风出口 1 m 以上，气流引起的温度梯度会被当成热源。"));
children.push(BULLET("避免正对玻璃、阳光直射与白炽灯等热辐射源，滤光片虽然截止可见光，但 7 ~ 14 µm 波段对热源毫无抵抗力。"));
children.push(BULLET("与雷达共壳时，PIR 窗口需与雷达天线罩分开布置，雷达罩材料应选低介电常数、厚度可控的 ABS 或 PC，避免金属漆与镀层。"));

children.push(H2("1.6  已知局限"));
children.push(P("频率响应集中在 0.4 ~ 7.0 Hz，意味着器件对“动的热源”敏感、对“静止的热源”不敏感。人静坐不动时输出趋于平缓，无法据此判断有人，这正是产品需要引入雷达做二次确认的根本原因。"));
children.push(P("此外，环境温度接近人体温度时差分信号会被压缩，灵敏度下降；器件本身也不具备测距能力，无法给出目标远近。这两点在规格书中均未给出补偿方案，属于整机设计需要覆盖的部分。"));

children.push(H1("第二章  毫米波雷达（E54-24LD12A）", { newPage: true }));

children.push(H2("2.1  器件定位"));
children.push(P("E54-24LD12A 由成都亿佰特电子科技有限公司生产，是基于 24GHz 毫米波传感器芯片开发的广覆盖人体微动传感器。模组采用 FMCW 调频连续波体制，片内集成一发一收天线、雷达信号处理与 MCU，直接输出有人无人状态与目标距离，开发者无需处理原始中频信号。"));
children.push(NOTE("说明：送审文件名称为 E54-24LD12C，文档封面与正文标题均为 E54-24LD12A。两者是否为同一系列的不同后缀，需向供应商书面确认，本文按正文的 E54-24LD12A 记述。"));

children.push(H2("2.2  关键参数"));

children.push(CAPTION("表 2-1  E54-24LD12A 规格参数"));
children.push(makeTable(
  [2400, 2500, 4126],
  ["参数", "数值", "条件与说明"],
  [
    ["支持频段", "24 ~ 24.25 GHz", "符合 FCC、CE 无委会认证标准"],
    ["最大扫频带宽", "0.25 GHz", "FMCW 体制"],
    ["最大等效全向辐射功率", "12 dBm", "EIRP"],
    ["供电电压", "3.0 / 3.3 / 3.6 V", "最小值 / 典型值 / 最大值"],
    ["平均工作电流", "50 mA", "连续工作状态"],
    ["外形尺寸", "20 × 20 mm", "公差 ±0.2 mm，重量 1.2 g"],
    ["环境温度", "-40 ~ 85 ℃", "工业级"],
    ["数据刷新周期", "100 ms", "即 10 Hz 输出"],
    ["探测范围（挂壁，运动）", "10 m", "运动人体目标，法向"],
    ["探测范围（挂壁，微动）", "6 m", "微动人体目标，法向"],
    ["探测范围（挂顶，运动）", "5 m", "运动人体目标"],
    ["探测范围（挂顶，微动）", "4 m", "微动人体目标"],
    ["探测精度", "0.15 m", "表 2.1 标称，10 m 内运动目标"]
  ]
));

children.push(H2("2.3  挂壁安装与覆盖范围"));
children.push(P("规格书第 6.2 节明确：推荐挂壁安装高度为 1.5 ~ 2.0 m。挂壁安装时，模组 X 轴指向水平方向，Z 轴向上，Y 轴指向检测区域，默认配置下最大运动感应范围为传感器法向 10 m、水平和俯仰方向夹角 ±60° 以内的圆锥形空间。"));
children.push(P("这一几何关系带来两个容易被忽略的推论。其一，挂高变化不改变水平覆盖半径，10 m 与 6 m 是法向距离，与高度无关；其二，波束下沿为 -60°，与地面交汇的距离随挂高变化，1.5 m 挂高时约 0.87 m，2.0 m 挂高时约 1.15 m，脚边这一圈属于几何弱覆盖区。"));

children.push(CAPTION("表 2-2  挂壁覆盖几何"));
children.push(makeTable(
  [2500, 2400, 4126],
  ["项目", "数值", "说明"],
  [
    ["推荐挂壁高度", "1.5 ~ 2.0 m", "低于 1.5 m 时微动灵敏度下降"],
    ["运动探测距离", "10 m（法向）", "对应图 6-4 的 10 m 标注"],
    ["微动探测距离", "6 m（法向）", "静止与小幅动作维持"],
    ["水平覆盖角", "±60°（合计 120°）", "图 6-5 外轮廓"],
    ["俯仰覆盖角", "±60°", "与水平角一致，构成圆锥"],
    ["波束下沿触地距离", "0.87 m（挂高 1.5 m）", "按 h / tan60° 计算"],
    ["波束下沿触地距离", "1.15 m（挂高 2.0 m）", "按 h / tan60° 计算"],
    ["120° 扇形面积", "约 105 m²（10 m）", "理论值，未扣除遮挡"],
    ["120° 扇形面积", "约 38 m²（6 m）", "微动覆盖，可作布点依据"],
    ["最近感应距离", "0.2 m", "规格书称无检测盲区"]
  ],
  { keepTogether: true }
));

children.push(P("图 6-5 的实测轮廓与标称值基本吻合，但呈现明显的角度衰减：0° 方向运动目标可达 10 m，30° 以内仍维持在 9 m 左右，到 60° 附近收缩至 6 m 上下，60° 以外迅速衰减。因此 120° 应理解为可靠触发角，外环 60° ~ 75° 只能当容错余量，不能作为设计覆盖使用。", { spacing: { line: 340, lineRule: LineRuleType.AUTO, before: 120, after: 120 } }));

children.push(H2("2.4  测距与识别精度"));
children.push(P("模组内部按距离门划分检测空间，共 16 个距离门，每门宽度 0.7 m，可通过配置选择 0 ~ 15 号门中的最大门限，对应最远约 10.5 m。上报的目标距离以厘米为单位，例如 0x0069 表示 105 cm。"));
children.push(P("关于精度，规格书内部存在两处不一致：表 2.1 标注探测精度 0.15 m，第 8.2 节则写明理论上测距精度约为 0.35 m，且受体型、姿态与雷达散射截面积波动影响。前者更接近距离门之间的插值分辨率，后者才是可承诺的实际误差。对外标称建议采用 0.35 m。"));
children.push(P("识别能力方面，模组输出的是单目标信息，即最近或最强的一个目标，不具备人数统计与目标区分能力。无人判定依靠可配置的超时时间，范围为 0 ~ 65535 s，超时后转为无人状态。"));

children.push(H2("2.5  接口与配置"));

children.push(CAPTION("表 2-3  接口与可配置项"));
children.push(makeTable(
  [2300, 2600, 4126],
  ["项目", "规格", "说明"],
  [
    ["供电", "3.3 V（3.0 ~ 3.6 V）", "平均电流 50 mA"],
    ["串口", "UART，115200，8N1", "3.3 V TTL 电平"],
    ["开关量输出", "OT2 引脚", "有人时输出高电平"],
    ["最大距离门", "0 ~ 15 可配", "每门 0.7 m"],
    ["无人延时", "0 ~ 65535 s 可配", "对应目标消失判定时间"],
    ["触发门限", "可配", "按灵敏度需求调整"],
    ["数据刷新", "100 ms", "固定周期上报"]
  ],
  { keepTogether: true }
));

children.push(H2("2.6  干扰与安装注意"));
children.push(BULLET("模组背面与侧面需做金属或高介电常数遮挡，避免波束穿透背板造成隔墙误检。"));
children.push(BULLET("不得正对大面积玻璃，水平偏移建议 30° 以上，玻璃对 24GHz 的穿透损耗差异会导致楼外走动被误判为室内目标。"));
children.push(BULLET("远离卷帘门、吊扇、管道等金属摆动体 2 m 以上，这类物体的多普勒特征与人体的低速微动高度相似。"));
children.push(BULLET("远离空调出风口与新风出口，气流本身不会触发雷达，但吹动的窗帘、纸张会。"));
children.push(BULLET("天线罩不得使用金属漆、导电镀层或含碳材料，罩体与天线之间需保留空气间隙。"));

children.push(H1("附录 A  与 PRD V2.5 的差异项", { newPage: true }));
children.push(P("将两份规格书与《澜潮_SKU2_双鉴存在传感器_PRD_V2.5》对照，存在四处需要确认的不一致，建议在开模与认证前闭环。"));
children.push(CAPTION("表 A-1  差异对照"));
children.push(makeTable(
  [1500, 2500, 2500, 2526],
  ["项目", "PRD V2.5", "规格书", "处理建议"],
  [
    ["雷达型号", "BOM 标注 RKB1161A3", "E54-24LD12A", "确认是否换料或并行评估"],
    ["侧装高度", "1.2 ~ 2.0 m", "1.5 ~ 2.0 m", "下限提高至 1.5 m，或补 1.2 m 实测数据"],
    ["雷达保持角", "≥ 150°", "±60°，合计 120°", "修改指标或更换模组"],
    ["测距精度", "未定义", "0.15 m 与 0.35 m 并存", "对外统一按 0.35 m 标称"]
  ],
  { keepTogether: true }
));

children.push(H1("附录 B  待实测项"));
children.push(P("以下四项无法从规格书推导，需在样机上实测确认，建议纳入 DVT 验证清单。"));
children.push(BULLET("PIR 实装透镜后，在 1.5 m、2.0 m、2.5 m 三个高度分别测定触发距离与有效触发角，用于验证 PRD 承诺的 120° 触发角。"));
children.push(BULLET("雷达在 1.5 m 挂高、正对玻璃与金属卷帘条件下的虚警率，规格书仅列出干扰源而未给出量化指标。"));
children.push(BULLET("微动 6 m 的实测复核。该值是存在检测的核心卖点，规格书未标注测试条件与目标动作幅度。"));
children.push(BULLET("PIR 与雷达共壳时，24GHz 天线罩开窗尺寸、材料厚度对探测距离与角度的影响。"));

children.push(new Paragraph({
  children: [R("本文数据均引自供应商规格书原文，未经二次标定。标注为推算的数值已在该处说明计算方法。", { size: 18, color: GREY })],
  spacing: { before: 360, after: 0, line: 280, lineRule: LineRuleType.AUTO },
  border: { top: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF", space: 10 } }
}));

const doc = new Document({
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font: SONG, size: 21, color: INK }, paragraph: { spacing: { line: 340, lineRule: LineRuleType.AUTO } } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HEI, size: 30, bold: true, color: NAVY },
        paragraph: { spacing: { before: 360, after: 200, line: 340, lineRule: LineRuleType.AUTO }, outlineLevel: 0, keepNext: true }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HEI, size: 25, bold: true, color: "2F5496" },
        paragraph: { spacing: { before: 280, after: 140, line: 320, lineRule: LineRuleType.AUTO }, outlineLevel: 1, keepNext: true }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HEI, size: 22, bold: true, color: "404040" },
        paragraph: { spacing: { before: 200, after: 100, line: 300, lineRule: LineRuleType.AUTO }, outlineLevel: 2, keepNext: true }
      }
    ]
  },
  numbering: {
    config: [
      {
        reference: "dot-bullet",
        levels: [
          {
            level: 0, format: LevelFormat.BULLET, text: "·", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 460, hanging: 300 } }, run: { font: SONG, size: 21, color: INK } }
          }
        ]
      }
    ]
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 720, footer: 720 }
        }
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [R("澜潮科技 · SKU2 双鉴存在传感器 · 关键参数解读", { size: 16, color: "808080" })],
              spacing: { after: 0, line: 240, lineRule: LineRuleType.AUTO },
              border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF", space: 4 } }
            })
          ]
        })
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { before: 0, after: 0, line: 240, lineRule: LineRuleType.AUTO },
              children: [
                new TextRun({ children: ["第 ", PageNumber.CURRENT, " 页  共 ", PageNumber.TOTAL_PAGES, " 页"], font: SONG, size: 18, color: GREY })
              ]
            })
          ]
        })
      },
      children: children
    }
  ]
});

Packer.toBuffer(doc).then(function (buf) {
  const out = process.argv[2];
  fs.writeFileSync(out, buf);
  console.log("written", out, buf.length);
});
