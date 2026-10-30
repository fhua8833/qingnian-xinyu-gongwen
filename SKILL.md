---
name: qingnian-xinyu-gongwen
version: 1.0.1
description: "Generate or audit official documents that must follow the Sichuan Normal University 'Qingnian Xinyu' student theory-preaching team document format (青年新语公文格式). Use only when the user explicitly asks for that format, including 四川师范大学青年新语宣讲团公文, 青年新语公文格式, 宣讲团文件格式, or to check an existing .docx against it. Produces a deterministic DOCX through a fixed generator with strict font, size, spacing, heading, table, image, signature, attachment, and duplex page-number rules. Do NOT use for general Word documents, resumes, general reports, PPT, general PDF editing, or designing new layouts."
description_zh: "生成或审查必须遵守四川师范大学“青年新语”大学生理论宣讲团文件格式（青年新语公文格式）的正式公文。仅在用户明确要求该格式时使用，包括“四川师范大学青年新语宣讲团公文”“青年新语公文格式”“宣讲团文件格式”，或要求检查现有 .docx 是否符合该格式。通过固定生成器和严格门禁产出确定性 DOCX，覆盖字体、字号、行距、标题、表格、图片、落款、附件和双面页码。不得用于普通 Word 文档、简历、一般报告、PPT、一般 PDF 编辑或自行设计版式。"
---

# 青年新语公文格式

标准名：`qingnian-xinyu-gongwen`。唯一格式依据：`references/source.pdf`（3页，SHA256 `6d655f189de45c4cb0c7cb9e41dcff17edd5882b00d173af4489b384463133d8`）。

**一句话总则：只允许本 skill 白名单内的格式；白名单外的一切格式一律不出现，也不“美化”、不“顺手调整”、不凭经验补全。**

本 skill 的目标不是“尽量像公文”，而是：条件齐全时生成可复核的规范文件；条件不齐时明确停止，绝不交付伪合格稿。

---

## 1. 具体使用场景

### 1.1 必须使用本 skill

满足任一条：

1. 用户明确要求按“四川师范大学‘青年新语’大学生理论宣讲团文件格式”排版、生成或改写正式公文。
2. 用户要求制作“青年新语”宣讲团的通知、方案、报告、总结、请示、函等正式文稿，并指定使用该文件格式。
3. 用户已有定稿文字，要求套用该格式输出 DOCX/PDF。
4. 用户要求检查现有 DOCX 是否符合该格式，或按该格式修正。
5. 用户点名“青年新语公文格式”“宣讲团文件格式”，或提供本 skill 的 `source.pdf` 作为格式依据。

### 1.2 禁止使用本 skill

1. 普通 Word 排版、简历、论文、海报、PPT、Excel、一般报告。
2. 用户没有要求该特定格式，只说“排得正式一点”“像公文一样”。
3. 用户要求封面、目录、红头、发文字号、印章、水印、横向页、分栏、五号正文等超出本格式依据的版式。
4. 用户拒绝确认 `references/layout-profile.md` 中 PDF 未明确规定的补充参数。
5. 缺少指定原字体，且用户不能提供合法 TTF/OTF 文件。
6. 只需 Markdown、纯文本或聊天内容，不需要 DOCX 成品。

若只是“想美化简历/报告”，直接说明本 skill 不适用，不要强行套用。

---

## 2. 绝对规则（任何步骤都不得违反）

1. **白名单封闭。** 文档只能含本 skill 生成的段落、标题、表格、图片、页脚；不得出现任何未列出的对象或样式。
2. **格式由代码决定，不由文字描述或模型审美决定。** 不得直接写 OOXML、不得用 Pandoc/通用 docx 模板重新渲染、不得用 Word 手工调整后回传。
3. **不得改 skill。** 任务中遇到规则不合适，停止并向用户说明；禁止临时改字体、字号、边距、颜色、对齐、编号方式或删除检查。
4. **不得近似替代字体。** 只允许 `方正小标宋简体`、`仿宋_GB2312`、`楷体_GB2312`、`黑体`、`Times New Roman` 的原字体文件；字体内部名可命中固定同家族别名表，但禁止 Noto、思源、系统“仿宋/楷体/宋体”、Liberation、改名字体、PDF 子集字体。
5. **不得伪造内容。** 标题、作者、单位、日期、表格数字、图片说明必须来自用户；缺失就问，禁止编造占位内容并交付。
6. **不得伪造用户确认。** `approval.confirmed_by` 必须是真实用户；不得替用户同意补充配置，不得复制示例中的确认字段。
7. **不得跳过门禁。** 字体检查、结构检查、渲染检查、逐页复核缺一不可；任何一步失败即停止，不得“先交付再说”。
8. **不得声称未验证的合格。** 只有 `release.py accept` 生成验收凭据后，才可称“验收流程完成”；仍不得声称程序替用户做了视觉审阅。
9. **一个文档一个格式。** 不得混入其他学校、其他年度或“常见公文格式”的参数。
10. **未允许即禁止。** 本 skill 没写“允许”的格式，默认不允许。不要用“合理推断”“通常做法”放行。

---

## 3. 目录、依赖与安装

```text
qingnian-xinyu-gongwen/
├── SKILL.md
├── README.md
├── LICENSE
├── NOTICE.md
├── requirements.txt
├── assets/
│   └── fonts/            # 五款原字体、manifest.json 哈希清单、来源说明
├── scripts/
│   ├── qnxy.py           # 唯一生成器、输入校验、字体检查、结构校验
│   ├── setup_fonts.py    # 校验随包字体哈希并生成 work/fonts.json
│   └── release.py        # 渲染门禁、PDF自动检查、逐页验收凭据
├── references/
│   ├── source.pdf          # 原始格式依据
│   ├── source-rules.md     # P01—P20 逐条规则与标准执行代码
│   ├── layout-profile.md   # PDF未明确、须用户确认的固定补充参数
│   └── input-contract.md   # JSON输入契约
├── examples/
│   ├── content.json        # 仅演示结构；故意未确认，不能直接构建
│   └── fonts.json          # 字体路径模板
└── tests/
    └── test_rules.py       # 24项正反向自动测试
```

首次使用在该 skill 根目录执行：

```bash
python -m pip install -r requirements.txt
python scripts/qnxy.py doctor
```

预期输出含 `"dependencies": "PASS"`。仍须另外具备本机 `fc-match`、`soffice`（LibreOffice）、`pdftoppm`（Poppler）用于最终渲染；缺少任何一个就停止并请用户安装，不能省略渲染验收。

运行单元测试（只在维护时执行；测试中的批准字段是测试夹具，不是用户授权）：

```bash
python -m unittest discover -s tests -v
```

预期 `Ran 24 tests ... OK`。

---

## 4. 标准执行流程（弱 agent 按顺序照做）

### Step 0：判断场景

- 不属于第1节使用场景 → 不使用本 skill。
- 属于 → 继续。
- 只要用户没有明确要求本格式，不得擅自启用。

### Step 1：索取内容与授权

向用户收取：标题、正文、可选个人名称、可选落款单位和真实日期、附件、图片、表格数据。不得代写具体业务内容。

同时展示 `references/layout-profile.md`，并只问一次：

> 原PDF未明确页边距、落款对齐及部分图表细节。是否同意本skill随附的 `qnxy-explicit-layout-v1` 补充配置（A4纵向、四边25.4毫米、正文首行两字、落款右对齐、图表及分页采用文中固定规则）？未同意前不会生成正式稿。

用户明确同意后，才可写入以下固定确认语：

```text
已阅读并同意 references/layout-profile.md 的全部补充规则
```

没有明确同意 → 停止。不得把“按青年新语格式做”解释为同意补充配置。

### Step 2：填写内容 JSON

严格按 `references/input-contract.md`。最小结构：

```json
{
  "profile": "qnxy-explicit-layout-v1",
  "approval": {
    "confirmed_by": "用户在对话中使用的真实称谓或姓名",
    "confirmation": "已阅读并同意 references/layout-profile.md 的全部补充规则"
  },
  "title": "用户确认的公文标题",
  "blocks": [
    {"type": "paragraph", "text": "用户确认的正文。"}
  ]
}
```

可选字段只有 `author`、`signature`、`attachments`。没有就删除，禁止填空字符串或 null。不要填写任何格式字段；填写 `font`、`size`、`color`、`margin` 等会直接报错。

运行：

```bash
python scripts/qnxy.py check-input --input work/content.json
```

预期：`INPUT PASS（仅内容结构通过，不代表文件验收）`。失败就按报错改内容，不得绕过。

### Step 3：检查原字体

**优先使用随包字体，不要重复向用户索取。** 先在 skill 根目录运行：

```bash
python scripts/setup_fonts.py
```

脚本按 `assets/fonts/manifest.json` 逐个核对 SHA256，并写出 `work/fonts.json`（绝对路径）。哈希不符立即退出，禁止替换字体、改路径或跳过校验。`work/fonts.json` 已存在且内容不同时脚本拒绝写入，须先人工确认再删除。随包资源不表示内容或版式补充规则已获用户确认，也不表示字体已获无限制商业授权，详见 `assets/fonts/README.md`。

Linux 渲染主机还须安装同一批字体（只复制这五个）：

```bash
mkdir -p "$HOME/.local/share/fonts/qingnian-xinyu-gongwen"
cp -n assets/fonts/*.ttf "$HOME/.local/share/fonts/qingnian-xinyu-gongwen/"
fc-cache -f "$HOME/.local/share/fonts/qingnian-xinyu-gongwen"
```

安装成功不代表验收通过，`release.py render` 仍会核对实际字体文件哈希。

仅在随包资源缺失或不适用时，才要求用户提供合法原字体（`.ttf` 或 `.otf`，不支持 `.ttc`），并自建 `work/fonts.json`：

```json
{
  "title": "/absolute/path/方正小标宋简体.ttf",
  "body": "/absolute/path/仿宋_GB2312.ttf",
  "kai": "/absolute/path/楷体_GB2312.ttf",
  "hei": "/absolute/path/黑体.ttf",
  "latin": "/absolute/path/Times New Roman.ttf"
}
```

五个键必须齐全，哪怕某角色本次未使用。运行：

```bash
python scripts/qnxy.py font-check \
  --input work/content.json \
  --fonts work/fonts.json
```

必须成功并记录五个字体文件的 SHA256。若报“缺少允许的家族名”或“缺少字形”，停止并向用户索取正确原字体；禁止换替代字体，禁止只改字体名。

### Step 4：构建 DOCX + 结构门禁

```bash
python scripts/qnxy.py build \
  --input work/content.json \
  --fonts work/fonts.json \
  --output work/青年新语公文.docx \
  --report work/build-report.json
```

要求：

- `--output`、`--report` 必须尚不存在；程序拒绝覆盖。
- 成功时报告 `structure: PASS`，但 `release_status` 一定是 `BLOCKED_PENDING_VISUAL_REVIEW`，这不是合格证。
- 失败即停止，按报错修内容或字体；禁止手工编辑 DOCX、解包改 XML、再打包，也禁止删掉报告重跑以掩盖问题。

对已有 DOCX 做独立复核：

```bash
python scripts/qnxy.py validate \
  --input work/content.json \
  --fonts work/fonts.json \
  --docx work/青年新语公文.docx \
  --report work/structure-report.json
```

`validate` 会按输入重建标准包并逐字节比对；任何手改、样式注入、添加宏/链接/媒体都会失败。

### Step 5：渲染门禁

```bash
python scripts/release.py render \
  --input work/content.json \
  --fonts work/fonts.json \
  --docx work/青年新语公文.docx \
  --outdir work/rendered
```

`work/rendered` 必须尚不存在。成功会生成：

- `青年新语公文.pdf`
- `page-1.png`、`page-2.png`……
- `render-audit.json`（状态固定为 `BLOCKED_PENDING_VISUAL_REVIEW`）
- `review-to-fill.json`

自动检查包括：PDF 字体是否全部嵌入且在白名单、A4 尺寸、每页页码是否为连续 `— n —`、四号14pt、Times New Roman、奇数页右空一字/偶数页左空一字、数字字母无字体回退、文字不越界。

渲染失败常见原因：字体未真正安装、`fc-match` 解析到别的文件、LibreOffice 不可用。逐项修复后重新使用新的输出目录；不得跳过渲染。

### Step 6：逐页真实审阅

必须逐张打开 `rendered/page-*.png`，逐页核对 `references/source-rules.md` 与下列九项。确认无误后，把 `review-to-fill.json` 中每页对应值改为 `true`，填写真实审阅者：

```json
{
  "reviewer": "实际逐页查看的人",
  "docx_sha256": "保持原值",
  "pdf_sha256": "保持原值",
  "pages": [
    {
      "page": 1,
      "fonts_and_sizes": true,
      "line_spacing_and_indents": true,
      "no_clipping_or_overlap": true,
      "headings_and_captions_stay_with_content": true,
      "table_borders_and_cells": true,
      "image_placement_and_proportions": true,
      "signature_two_blank_lines": true,
      "attachment_starts_new_page": true,
      "odd_even_page_number": true
    }
  ]
}
```

九项含义：

1. `fonts_and_sizes`：标题、作者、正文、四级标题、表格、图表题、页码字体字号全部吻合。
2. `line_spacing_and_indents`：标题32pt、其余正文28pt固定行距；缩进为2字符，不是空格。
3. `no_clipping_or_overlap`：无文字/图片裁切、重叠、越界、空白页、孤立逗号。
4. `headings_and_captions_stay_with_content`：标题不悬页尾；图注不被拆到下一页；表题与表同页。
5. `table_borders_and_cells`：0.25磅全框线、仅表头行加粗、表头行以下（含首列）不加粗、两字项对齐、表格未越版心。
6. `image_placement_and_proportions`：正文图上下环绕且位于标题后正文前；表格图不越界；图片无拉伸。
7. `signature_two_blank_lines`：正文末段后正好两个真实空段，落款完整同页。
8. `attachment_starts_new_page`：每个附件新起一页，无额外空白页。
9. `odd_even_page_number`：每页页码正确，奇右偶左，空一字。

没有真实逐页查看，禁止全部改 `true`。这一步不能用自动检查替代。

### Step 7：生成验收凭据

```bash
python scripts/release.py accept \
  --input work/content.json \
  --fonts work/fonts.json \
  --docx work/青年新语公文.docx \
  --pdf work/rendered/青年新语公文.pdf \
  --audit work/rendered/render-audit.json \
  --review work/rendered/review-to-fill.json \
  --output work/acceptance.json
```

成功输出 `RELEASED_WITH_RECORDED_VISUAL_REVIEW`。程序会再次核对内容、字体、DOCX、PDF、截图哈希和九项复核；任何一项不齐都失败。该凭据只证明证据链完整，不证明审阅者真的看过每一页；不得伪造人工审阅。

### Step 8：交付

用 DeliverArtifacts 交付：`青年新语公文.docx`、`青年新语公文.pdf`、`acceptance.json`。回复中说明：该文件按 `qnxy-explicit-layout-v1` 生成；字体和页码已通过检查；逐页审阅记录已附；未使用白名单外格式。

---

## 5. 二十项格式与唯一执行代码

### 5.1 表格加粗的唯一规则（最高优先级，不得变通）

**整张表只有表头行加粗。表头行以下的所有行，包括第一列（标题列），一律常规不加粗。**

| 位置 | 加粗 | 依据 |
|---|---|---|
| 表头行（第一行） | 加粗 | `ROLES['cell_header']`，`row_header` 无影响 |
| 表头行以下所有行 | 不加粗 | `ROLES['cell']`，含 `row_header=true` 时的首列 |
| 表名、表内图注 | 不加粗 | `caption` |

- 判断条件只能是行号：`role = 'cell_header' if row_idx == 0 else 'cell'`。
- `row_header` 只用于“首列是否为语义标题列、是否参与两字对齐（P16）”，**不再决定加粗**。
- 禁止的理由与借口：“首列像标题所以加粗”“表头列更醒目”“和 Excel 习惯一致”“整行加粗更整齐”。
- 第一列不加粗不等于可以删掉该列或改用它做合并、斜线、嵌套。
- 违反即判失败；`test_table_rules` 会因首列 `w:b` 为 `1` 直接报错。

### 5.2 二十项格式与唯一执行代码

以下参数是封闭值。**任何一项都不得由模型另算、另填或“优化”。**

单位：字号为半磅；行距与缩进为 twip；边框单位是 1/8 磅。1pt=20twip。

```python
# scripts/qnxy.py —— 唯一允许的角色参数
ROLES = {
    'title':       ('title', 44, 640, 'center', 0,   False),  # P01 二号22pt/32pt
    'author':      ('kai',   32, 560, 'center', 0,   False),  # P02 三号16pt/28pt
    'body':        ('body',  32, 560, 'both',   200, False),  # P03 三号/28pt/首行2字
    'h1':          ('hei',   32, 560, 'both',   200, False),  # P04 黑体
    'h2':          ('kai',   32, 560, 'both',   200, False),  # P05 楷体
    'h3':          ('body',  32, 560, 'both',   200, False),  # P06 仿宋
    'h4':          ('body',  32, 560, 'both',   200, False),  # P07 仿宋
    'signature':   ('body',  32, 560, 'right',  0,   False),  # P09
    'blank':       ('body',  32, 560, 'both',   0,   False),  # P09 真实空段
    'attachment':  ('body',  32, 560, 'both',   200, False),  # P10
    'caption':     ('body',  21, 320, 'center', 0,   False),  # P12/P18 五号
    'cell':        ('body',  28, 400, 'center', 0,   False),  # P14 四号
    'cell_header': ('body',  28, 400, 'center', 0,   True),   # P13 仅表头行加粗
    'page_odd':    ('latin', 28, 400, 'right',  0,   False),  # P11
    'page_even':   ('latin', 28, 400, 'left',   0,   False),  # P11
}
```

|编号|格式要求|唯一执行代码/落点|机器检查|
|---|---|---|---|
|P01|大标题：方正小标宋简体，二号22pt，居中，固定32磅|`ROLES['title']`；`Builder.build`首段|`test_title_style`|
|P02|个人名称：楷体_GB2312，三号16pt，居中，固定28磅；可省略|`ROLES['author']`；`if 'author' in d`|`ROLES`参数固定|
|P03|正文：仿宋_GB2312三号，固定28磅，两端对齐，首行2字符|`ROLES['body']`；`paragraph(..., 'body')`|`test_body_and_heading_indent`|
|P04|一级标题：“一、”，黑体三号，首行2字符|`ROLES['h1']`；`heading_label(1,n)`|`test_numbering`|
|P05|二级标题：“（一）”，楷体_GB2312三号，首行2字符|`ROLES['h2']`；`heading_label(2,n)`|`test_numbering`|
|P06|三级标题：“1.”，仿宋_GB2312三号，首行2字符|`ROLES['h3']`；`heading_label(3,n)`|`test_numbering`|
|P07|四级标题：“（1）”，仿宋_GB2312三号，首行2字符|`ROLES['h4']`；`heading_label(4,n)`|`test_numbering`|
|P08|数字及字母全篇 Times New Roman，字号/加粗随所在角色|`run_properties`写全`ascii/hAnsi/cs`；`add_text`逐字分段|`test_latin_runs`；PDF回退检查|
|P09|落款：仿宋三号；正文末段后空两行|两个`ROLES['blank']`段＋`signature`；`keepNext`锁同页|`test_signature_exactly_two_real_blank_paragraphs`|
|P10|附件：另起一页；“附件1：XXXX”仿宋三号，首行2字符|`page_break=True`；`attachment`|`test_attachment_break`|
|P11|页码：页脚，双面，`— 1 —`，TNR四号，奇右偶左空一字|奇偶footer＋`PAGE`域＋280twip缩进|`test_duplex_footer`；PDF逐页检查|
|P12|表名：仿宋_GB2312五号10.5pt，不加粗，居中；表号全文连续，和名称空一格|`ROLES['caption']`；`f'表{n} '+caption`|`test_table_rules`|
|P13|表头行（表格第一行）：仿宋四号14pt，加粗，水平居中|`cell_header`；仅`row_idx == 0`|`test_table_rules`|
|P14|表正文（表头行以下的全部行，含首列数据）：仿宋四号，**必须不加粗**，水平居中|`ROLES['cell']`；`role = 'cell_header' if row_idx == 0 else 'cell'`|`test_table_rules`|
|P15|表边框0.25磅；表内数字TNR|`w:sz="2"`六边框；`add_text`|`test_table_rules`|
|P16|两字项目与三字对齐（如“名　称”）：仅表头行/标题列；只影响对齐，不影响加粗|表头或标题列单元格纯2汉字→中间U+3000|`test_table_rules`|
|P17|正文图片：居中，文字环绕上下型；标题下、正文上|`picture(..., floating=True)`→`wp:anchor`+`wrapTopAndBottom`|`test_body_image_anchor_not_inline`|
|P18|正文图注：仿宋五号不加粗居中；图号全文连续空一格|`f'图{n} '+caption`；`caption`|`test_body_image_anchor_not_inline`|
|P19|表内图片：各行长宽一致、单元格水平垂直居中、不越框|同表统一显示尺寸；`wp:inline`；`vAlign=center`|`test_table_images_equal_sizes_inline_center`|
|P20|表内图注：五号居中，序号从表标题行起依次排列，空一格|每表`local_fig`从1按行/列递增|`test_table_images_equal_sizes_inline_center`|

### 5.3 段落与字体底层代码（不允许改写）

```python
def run_properties(role, size, bold=False):
    p = el('w:rPr')
    sub(p, 'w:rFonts', {
        'w:ascii': 'Times New Roman', 'w:hAnsi': 'Times New Roman',
        'w:eastAsia': FONTS[role], 'w:cs': 'Times New Roman',
        'w:hint': 'eastAsia'})
    sub(p, 'w:b',  {'w:val': '1' if bold else '0'})
    sub(p, 'w:bCs',{'w:val': '1' if bold else '0'})
    sub(p, 'w:i',  {'w:val': '0'})
    sub(p, 'w:color', {'w:val': '000000'})
    sub(p, 'w:spacing', {'w:val': '0'})
    sub(p, 'w:w', {'w:val': '100'})
    sub(p, 'w:sz', {'w:val': size})
    sub(p, 'w:szCs', {'w:val': size})
    sub(p, 'w:u', {'w:val': 'none'})
    sub(p, 'w:vertAlign', {'w:val': 'baseline'})
    sub(p, 'w:lang', {'w:val': 'en-US', 'w:eastAsia': 'zh-CN'})
    return p

def paragraph(value, role, keep=False, page_break=False):
    font, size, line, align, indent, bold = ROLES[role]
    # spacing: before=0 after=0 line=line lineRule="exact"
    # ind: firstLine=size*20 if indent, firstLineChars=indent (200 = 2字符)
    # jc: center/both/right/left
    # 标题追加 outlineLvl = level-1
```

`firstLineChars="200"` 是“2字符”的唯一实现；不允许用两个空格或全角空格冒充。所有段落 `before=0`、`after=0`，不允许 Word 默认段后距。

### 5.4 页码底层代码（不允许改写）

```python
# settings.xml 必须含 evenAndOddHeaders
# sectPr 同时引用 footer1(默认/奇数) 与 footer2(偶数)
p = paragraph('— ', 'page_even' if even else 'page_odd')
field = sub(p, 'w:fldSimple', {'w:instr': ' PAGE ', 'w:dirty': 'true'})
add_text(field, '2' if even else '1', 'latin', 28)   # 域缓存，不是静态页码
add_text(p, ' —', 'latin', 28)
```

`—` 与数字之间是一个半角空格；四号是28半磅；空一字用280twip缩进，不是空格、不是16pt。

### 5.5 表格底层代码要点

```python
# 0.25磅 = w:sz="2"；外框和内框全部设置
for side in ['top','left','bottom','right','insideH','insideV']:
    sub(borders, 'w:'+side, {'w:val':'single','w:sz':'2',
                             'w:space':'0','w:color':'000000'})
# 加粗只作用于表头行：role = 'cell_header' if row_idx == 0 else 'cell'
# 表格居中、固定布局、宽度=版心9026twip；等宽列，末列吸收舍入差
# 单元格水平居中用段落 jc=center；垂直居中用 <w:vAlign w:val="center"/>
# 表头行重复 <w:tblHeader/>；行不跨页 <w:cantSplit/>
```

---

## 6. 明确禁止出现的格式（零容忍）

以下内容无论看起来多合理，均不得出现在成品中。出现即判失败，必须停止并重做。

### 6.1 文档结构

- 封面、封二、目录、摘要独立页、正文前空白页、独立附件封面
- 红头、红色分隔线、发文字号、签发人、密级、紧急程度、版记、印章、签名章、水印
- 页眉、页眉线、页眉文字、页码以外的页脚内容
- 分栏、横向页、多节版式、文字方向变更、页面边框、底纹、页面颜色
- 脚注、尾注、批注、修订痕迹、文档属性中的自定义字段
- 超链接、书签目录、交叉引用、域（PAGE 页码域除外）、宏、OLE、ActiveX、嵌入文件、外部关系
- 文本框、形状、SmartArt、图表对象、艺术字、公式对象、二维码
- 自动多级列表、项目符号、编号列表、任务清单、表格作为布局工具
- 五级及以下标题、行内标题、跳级标题、手写标题序号
- 空段（仅允许落款前两个和图片承载段）、手动换行、连续分页符、用空格制造缩进/居中/空行
- 任何未在本 skill 声明的样式、主题、字体嵌入以外的自定义部件

### 6.2 文字格式

- 非黑色文字、彩色文字、高亮、底纹、描边、阴影、发光
- 加粗（仅表格第一行表头允许；表头行以下任何单元格、任何列都不得加粗）、斜体、下划线、删除线、双删除线、上标、下标、小型大写、全部大写
- 字符缩放、字距调整、分散对齐（正文必须两端对齐）、右缩进/左缩进（页码空一字除外）
- 段前段后间距、1.5倍行距、最小值行距、多倍行距（必须固定值）
- 手打空格对齐、全角空格排版（两字表格项由程序插入者除外）、制表符
- 中西文自动间距、中文与数字自动加空、标点压缩
- 任意字体回退、字体替换、字体缺失时“能看就行”
- 白色文字、隐藏文字、零宽字符、方向控制符

### 6.3 表格

- 合并单元格、斜线表头、嵌套表格、拆分表格、无线框表格
- 彩色边框、粗细不是0.25磅的边框、只设外框不设内框、灰色边框
- 固定行高导致裁切、行跨页、表头不重复、表格超出版心
- 表内多段正文、表内项目符号、表内标题样式、表内空单元格占位
- 表名带手写“表1”、表名与表号之间无空格或多空格、表号按章节重置
- 首列或任意数据行被加粗；整表加粗；用加粗冒充表头
- 表内图片拉伸、裁切、加白边补齐、超出单元格；同一张表内图片尺寸不一致
- 用图片代替可编辑表格

### 6.4 图片

- 正文图使用嵌入型（`wp:inline`）冒充上下型环绕
- 正文图不在标题之后、正文之前；图片与图注分离；图注在上方
- 图注不带图号、图号手填、图号与名称之间无空格
- 图片带边框、阴影、三维效果、旋转、翻转、透明色、水印
- 图片超出页面/版心、遮挡文字、与文字重叠
- 用截图承载公文正文、用图片规避字体规则

### 6.5 落款、附件、页码

- 落款不右对齐、日期格式非“2026年10月28日”、月份/日期补零
- 用段前距、空行符或若干空格冒充“空两行”
- 落款与正文最后一行分页
- 附件不另起一页、附件序号手写、附件标记缩进错误
- 静态页码、每页都写“1”、奇偶页脚相同、页码非四号、页码非TNR
- 页码贴边、无空一字、用全角空格或正文16pt实现空一字
- 把“双面打印”误解为设置打印机，而不是奇偶页脚

> 若用户要求上述任何一项，回答：该格式不在本 skill 的格式依据内，当前版本不能生成；如确需，请提供新的正式格式依据，由规范维护者升级 skill。不要“只做一点点”。

---

## 7. 自动化门禁实际检查什么

`qnxy.py`：

- 输入字段白名单、重复键、类型、长度、控制字符、Markdown/HTML、首尾空格、连续空格、全角空格。
- 标题级别1—4、不得跳级、不得手写序号、标题后必须有内容。
- 图片存在、在输入目录内、PNG/JPEG、非动画、像素上限；正文图片固定“标题→图→正文”位置；表内图宽高比一致。
- 表格矩形、1—200行、1—6列、无合并、表头行加粗且其余行不加粗、标题列语义、图片单元格不越界。
- 字体文件为绝对路径 TTF/OTF、内部字体名在白名单、所需字形齐全、记录SHA256。
- DOCX 包部件白名单，禁止宏/链接/额外媒体；逐字节重建比对，拒绝任何手改。
- 日期真实有效；落款、附件、作者等结构合法。

`release.py`：

- `fc-match` 解析到的实际字体文件哈希必须与 `fonts.json` 一致。
- LibreOffice 转 PDF；PDF 字体全部嵌入且名称在白名单；数字字母无回退。
- A4；每页页码为连续 `— n —`；四号14pt；TNR；奇右偶左空一字；文字不出页面。
- 生成逐页 PNG 和哈希；`accept` 再核 DOCX/PDF/截图哈希及九项逐页复核。

程序通过 ≠ 视觉合格；必须完成 Step 6。程序失败 ≠ 可以放宽标准；必须修复或停止。

---

## 8. 标准失败处置

|失败信息|含义|唯一正确动作|
|---|---|---|
|`必须先取得用户真实确认`|没有合法补充配置授权|向用户展示配置并请求确认；不得改JSON绕过|
|`含未授权字段`|输入夹带格式|删除该字段；不得扩展契约|
|`正文不得冒充带编号标题`|手写了“一、”等|改用`heading`并去掉序号|
|`标题不得跳级`|结构错误|调整层级或询问用户|
|`正文图片必须紧接所属标题`|图片位置没有依据|移到规定位置或删除|
|`同一表内所有图片宽高比必须一致`|图片会变形|请用户换同比例原图；不得裁切/拉伸|
|`字体缺少允许的家族名`|替代字体或名字被改|索取原字体；不得改名或换近似|
|`指定字体缺少字形`|字体不完整|换合法完整原字体；不得让系统回退|
|`渲染主机未真正使用指定字体`|`fc-match`解析错误|正确安装同一字体文件后重跑|
|`DOCX包部件白名单不匹配`|文档被手改/夹带|从输入重新生成；不得手工修补|
|`与确定性规范不一致`|手改或旧版本生成|重新构建；不得放宽比对|
|`第n页页码不正确`|域未更新/版式错|修生成器问题或更换渲染环境；不得静态补数字|
|`复核记录与当前文件不匹配`|文件在复核后被改|重新渲染、重新逐页审阅|
|`第n页仍有未完成或未通过项`|复核未做完|实际查看并修复，不得直接改true|

任何“重试直到成功”都必须基于修复原因；禁止删除检查、改测试、改期望值、改 skill 参数。

---

## 9. 交付前自检（逐项打勾，缺一不可）

- [ ] 用户明确要求“青年新语”格式，不是普通公文。
- [ ] 用户明确同意 `qnxy-explicit-layout-v1`，确认记录属实。
- [ ] 五个原字体为合法 TTF/OTF，`font-check` 通过，哈希已记录。
- [ ] `check-input`、`build`、`validate` 全部通过，无覆盖输出。
- [ ] `render` 通过，字体、页码、A4、越界自动检查通过。
- [ ] 表格只有表头行加粗，表头行以下全部常规，未把首列当表头。
- [ ] 已逐页打开 PNG，九项全部真实核对。
- [ ] `accept` 生成验收凭据。
- [ ] 交付 DOCX、PDF、验收凭据三件套。
- [ ] 回复中未夸大：没有声称程序代替人工视觉审阅。
- [ ] 成品无第6节任何禁止格式。

---

## 10. 常见错误，发现即重做

1. 用普通“仿宋”代替“仿宋_GB2312”，或用“宋体”代替“方正小标宋简体”。
2. 把“二号”写成22号字（实际22pt、`w:sz=44`）。
3. 把“固定值28磅”写成1.5倍行距或最小值。
4. 用两个空格代替2字符首行缩进。
5. 把“空两行”做成段前56pt，或插入3个以上空段。
6. 页码直接手打，不用 PAGE 域；奇偶页脚相同。
7. 正文图用嵌入型，或把图注放图上方。
8. 表名写“表1：xxx”“表 1 xxx”，标点/空格不符。
9. 表格只设外框，内框默认0.5磅。
10. 两字单元格写成“名 称”两个半角空格，而不是程序插入的全角空格。
11. 表内图片拉伸到同宽同高，破坏原比例。
12. 手工编辑 DOCX 后仍用旧报告验收。
13. 缺少字体时下载“相似字体”或提取 PDF 子集字体。
14. 看到“自动检查通过”就跳过逐页审阅。
15. 为赶进度伪造 `approval`、`reviewer` 或九项 `true`。
16. 把首列当成“标题列”加粗，或整表加粗；本格式只有表头行加粗，其余一律常规。

---

## 11. 依据边界声明

- 本 skill 只对上述 PDF 明确规则及其经用户确认的补充配置负责；不声称代表四川师范大学其他文件，也不声称是通用党政机关公文格式。
- PDF 未明确的内容（页边距、落款对齐、日期样式、图注行距、表内图号算法等）全部固定在 `references/layout-profile.md`，不得由模型现场发挥。
- 本 skill 不授予字体版权；用户须自行确保字体合法可用。
- 不能保证任意 Word/WPS/LibreOffice 版本像素级一致；能保证在字体齐备、门禁通过、逐页复核完成前，不会把文件标为合格。

需要逐条原文与完整代码时，读 `references/source-rules.md`；需要字段细节时，读 `references/input-contract.md`；需要确认参数时，读 `references/layout-profile.md`。
