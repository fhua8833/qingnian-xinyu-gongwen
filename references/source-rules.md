# 原PDF逐项规则与执行绑定

唯一格式依据：用户提供的《四川师范大学“青年新语”大学生理论宣讲团文件格式 (1).pdf》，共3页。本包保留原文件为 `references/source.pdf`。规则按原文的明确描述，而非按PDF内部提取出的15.95pt等浮点近似值执行。

原文中的“仿宋 GB-2312”“仿宋-GB-2312”统一实现为Word字体族`仿宋_GB2312`；“楷体 GB-2312”实现为`楷体_GB2312`。不代表允许普通“仿宋”或普通“楷体”替代。字体文件中的同族中英文名可经固定别名表核验。

## 单位换算

```python
# DOCX w:sz / w:szCs 的单位为半磅
二号 = 22.0; 三号 = 16.0; 四号 = 14.0; 五号 = 10.5
字号XML = {"二号": 44, "三号": 32, "四号": 28, "五号": 21}
# 1pt = 20twip；边框 w:sz 的单位为1/8pt
标题行距 = 32 * 20        # 640，lineRule必须exact
正文行距 = 28 * 20        # 560，不能写成1.5倍/最小值
表格边框 = int(0.25 * 8)  # 2，不能写成0.25或4
两字首行缩进 = 200        # firstLineChars以1/100字符计
```

以下代码是 `scripts/qnxy.py` 的调用/核心实现绑定，不是让agent重新编写一套生成器。正式文档只能通过命令行入口构建；下列片段不得被拼接为绕过字体门禁的替代路径。

## P01 文档标题（第1页）

原文：方正小标宋简体，二号，段落居中对齐，行间距固定值32磅。

```python
# ROLES：字体角色、半磅字号、twip行距、对齐、首行字符百分数、加粗
ROLES['title'] = ('title', 44, 640, 'center', 0, False)
body.append(paragraph(data['title'], 'title', keep=True))
```

`title`是实际公文标题，不得把模板说明“方正小标宋……”当标题内容。允许自动折行，禁止添加封面或副标题样式。

## P02 个人名称（第1页）

原文：个人名称（如有）；楷体 GB-2312，三号，段落居中对齐，固定28磅。

```python
ROLES['author'] = ('kai', 32, 560, 'center', 0, False)
if 'author' in data:
    body.append(paragraph(data['author'], 'author', keep=True))
```

没有姓名就不输出该段；禁止擅填作者或用单位名冒充个人名称。

## P03 正文（第1页）

原文：仿宋 GB-2312 三号，固定28磅，两端对齐。

```python
ROLES['body'] = ('body', 32, 560, 'both', 200, False)
body.append(paragraph(block['text'], 'body'))
# 上面的200首行缩进是经确认的补充规则，不是本条原文字句。
```

## P04—P07 四级标题（第1页）

原文依次为：“一、”黑体三号；“（一）”楷体 GB-2312三号；“1.”仿宋 GB-2312三号；“（1）”仿宋 GB-2312三号。四者段落首行均缩进2字符。

```python
ROLES['h1'] = ('hei', 32, 560, 'both', 200, False)
ROLES['h2'] = ('kai', 32, 560, 'both', 200, False)
ROLES['h3'] = ('body', 32, 560, 'both', 200, False)
ROLES['h4'] = ('body', 32, 560, 'both', 200, False)
value = heading_label(level, counters[level-1]) + block['text']
body.append(paragraph(value, 'h'+str(level), keep=True))
# paragraph实际写入：
# <w:ind w:left="0" w:right="0" w:firstLine="640" w:firstLineChars="200"/>
```

不允许仅输入两个空格代替缩进。第三级的点为半角`.`；第二、四级括号为全角`（）`。`firstLineChars=200`为精确字符单位，`firstLine=640`是16pt下的32pt兼容表达，不能写成悬挂缩进。

## P08 全文数字及字母（第1页）

原文：全文数字及字母字体均为 Times New Roman。

```python
# 所有角色的基础rFonts都设置：
sub(p, 'w:rFonts', {
    'w:ascii': 'Times New Roman', 'w:hAnsi': 'Times New Roman',
    'w:eastAsia': FONTS[role], 'w:cs': 'Times New Roman',
    'w:hint': 'eastAsia'
})
# add_text逐字分段；数字和非CJK字母单独设为latin角色，避免全角数字走中文字体。
selected = font_role(c, role)
```

覆盖标题、作者、正文、所有标题序号、图表号、表格数字、落款日期、附件标记和页码。字号和加粗遵循所在内容角色；不是“遇到数字一律四号”。源图片内部的像素文字无法通过DOCX字体属性控制，不允许用图片替代公文正文规避本规则。

## P09 落款（第1页）

原文：仿宋 GB-2312三号，与正文最后一行空两行。

```python
body.append(paragraph('', 'blank', keep=True))
body.append(paragraph('', 'blank', keep=True))
body.append(paragraph(data['signature']['organization'], 'signature', keep=True))
body.append(paragraph(f'{y}年{m}月{day}日', 'signature'))
```

严格为两个空段、每段28pt；单位与日期右对齐为补充配置。无落款时不生成空段。不得编造单位、日期或落款人。

## P10 附件（第1页）

原文：另起一页，注附件1：XXXX，仿宋 GB-2312三号，首行缩进2字符。

```python
body.append(paragraph(f'附件{n}：'+attachment['title'],
                      'attachment', keep=True, page_break=True))
# <w:pageBreakBefore w:val="1"/>
```

分页通过段前分页属性，不插一堆回车。每个附件从新页开始，标题序号由程序生成。

## P11 页码（第1页）

原文：页脚，“双面打印”，“— 1 —”，Times New Roman四号；单页居右空一字，双页居左空一字。

```python
# settings和节关系：
sub(settings, 'w:evenAndOddHeaders')
sub(sect, 'w:footerReference', {'w:type': 'default', 'r:id': 'rOdd'})
sub(sect, 'w:footerReference', {'w:type': 'even', 'r:id': 'rEven'})
# 页码段落：奇数right并right=280；偶数left并left=280。
p = paragraph('— ', 'page_even' if even else 'page_odd')
field = sub(p, 'w:fldSimple', {'w:instr': ' PAGE ', 'w:dirty': 'true'})
add_text(field, '2' if even else '1', 'latin', 28)  # 这里只是域缓存，不是静态页码
add_text(p, ' —', 'latin', 28)
```

必须用PAGE域，不能把“— 1 —”静态复制到所有页。实际页码由渲染器更新；`release.py`按每页序号、字体、字号、位置复核。“双面打印”落实为奇偶页脚，并不是给操作系统设置打印机的双面选项。

## P12 表格名称（第2页）

原文：仿宋-GB-2312五号，不加粗，水平居中；表序号从全文依次排列，与名称之间空一格。

```python
self.table_no += 1
self.body.append(paragraph(f'表{self.table_no} '+block['caption'], 'caption', keep=True))
# ROLES['caption'] = ('body', 21, 320, 'center', 0, False)
```

表题在上方由原例示范、在补充配置中固定；从1开始，不照抄示例图中的“表9”。

## P13 表头行（第2页）

原文：仿宋-GB-2312四号，加粗，水平居中。原文“加粗”只针对表头行，未对首列或其他行提出加粗要求。

```python
role = 'cell_header' if row_idx == 0 else 'cell'
tc.append(paragraph(cell, role))
# ROLES['cell_header'] = ('body', 28, 400, 'center', 0, True)
```

只有第一行是表头；`row_header=true` 时首列是语义标题列，用于两字对齐（P16），但**不加粗**。不得以“首列像标题”为由补加粗，也不得整表加粗。

## P14 表格正文（第2页）

原文：仿宋-GB-2312四号，不加粗，水平居中。

```python
ROLES['cell'] = ('body', 28, 400, 'center', 0, False)
tc.append(paragraph(cell, 'cell'))   # 表头行以下全部行，含首列
```

## P15 边框和表内数字（第2页）

原文：表格边框0.25磅；数字格式Times New Roman。

```python
for side in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
    sub(borders, 'w:'+side, {'w:val': 'single', 'w:sz': '2', 'w:space': '0', 'w:color': '000000'})
# 单元格文本同样通过add_text，数字使用Times New Roman，字号28半磅。
```

禁止默认0.5pt、只改外边框、不改内边框、边框颜色灰色等“近似”。

## P16 两字项目对齐（第2页）

原文：两字符均与三字符对齐，例如“名 称”。

```python
if (row_idx == 0 or (block['row_header'] and col == 0)) and re.fullmatch(r'[\u3400-\u9fff]{2}', cell):
    cell = cell[0]+'\u3000'+cell[1]
```

只处理表头行和经确认的标题列，普通数据单元格“北京”不得变成“北　京”。固定三字宽的实现见补充配置；只有生成器可插入该全角空格，用户正文输入不能据此添加任意空格排版。

## P17 正文图片（第2页）

原文：水平居中、文字环绕为上下型；列于各级标题以下、正文以上。

```python
# validate_blocks要求：heading -> figure -> paragraph
body.append(self.picture(image, *self.image_geometry(image, TEXT_W), floating=True))
# picture内部必须同时出现：
# <wp:anchor ...><wp:positionH relativeFrom="column"><wp:align>center</wp:align>
# ...<wp:wrapTopAndBottom/>...</wp:anchor>
```

不能用`wp:inline`冒充正文图片上下环绕。位置检查是输入结构规则，不让agent凭视觉“差不多”决定。

## P18 正文图注（第2页）

原文：图片正下方按主要内容命名；仿宋-GB-2312五号，不加粗，水平居中；图号从全文依次排列，与名称之间空一格；数字Times New Roman。

```python
self.fig_no += 1
body.append(paragraph(f'图{self.fig_no} '+image['caption'], 'caption', keep=True))
```

不从原PDF图2继续编号；新公文从图1开始。标题、图、图注及图后正文首行必须保持合理邻接，不能把图注留到下一页。

## P19 表内图片（第2—3页）

原文：各行图片长宽一致；单元格水平垂直居中；不超出单元格边框。

```python
# 验证同表内原图宽高比完全一致；渲染尺寸由同一算法确定。
need(all(w2*h == w*h2 for w2,h2 in pictures), '宽高比不一致')
sub(tcpr, 'w:vAlign', {'w:val': 'center'})
tc.append(self.picture(cell['image'], *dimensions, floating=False))
# table图片：wp:inline；段落center；尺寸≤列宽-左右内边距。
```

不拉伸、裁切、越界；尺寸和可见边框均需渲染复核。

## P20 表内图注及序号（第2—3页）

原文：图下按主要内容命名；仿宋-GB-2312五号、不加粗、水平居中；图序号“需从所在表格标题行角度依次排列”，图序号与名称之间空一格。

```python
local_fig = 0  # 每个表独立建立
# 遍历正文行，从上到下；每行从左到右：
local_fig += 1
tc.append(paragraph(f'图{local_fig} '+cell['image']['caption'], 'caption'))
```

原文没有明说“每表重置”或“每行重置”，本版本必须先取得用户对补充配置的确认，再执行上述确定算法；不得把该解释写成原文逐字规定。

## 原文没有授权的内容

PDF中的说明文字、例图颜色、示例“表9”“图2”、示例页码和范例名称均不是新公文必须复制的内容。原PDF没有给出页边距数值、正文首行缩进的明确总规则、落款对齐、日期样式、表格列宽行高、图注行距等，必须使用经确认的补充配置，不能援引“常见公文格式”自动补全。
