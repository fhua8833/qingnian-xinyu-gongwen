# 输入契约：只能填内容，不能传格式

编码UTF-8，标准JSON；禁止重复键、注释、尾逗号。根对象只接受：

- 必填：`profile`、`approval`、`title`、`blocks`。
- 可选：`author`、`signature`、`attachments`。没有就删除该字段，不能填空字符串或null。
- 任意额外字段，包括`font`、`size`、`style`、`margin`、`bold`、`color`、`line_spacing`，立即报错。

`profile`只能是`qnxy-explicit-layout-v1`。`approval`仅接受`confirmed_by`和`confirmation`；后者在用户真实确认后固定填写`已阅读并同意 references/layout-profile.md 的全部补充规则`。`confirmed_by`记录用户真实称谓或用户本人，不伪造姓名，不填写agent作为用户确认人。

## 内容块

正文普通段：

```json
{"type":"paragraph","text":"这里是已经定稿的正文。"}
```

独立标题：

```json
{"type":"heading","level":1,"text":"工作安排"}
```

`level`仅允许整数1、2、3、4；禁止首个标题从二级开始；禁止一级直接跳三级。`text`不含“一、”“（一）”“1.”“（1）”，序号由程序产生。不要为了模仿标题把编号写进普通正文。

正文图片：

```json
{"type":"figure","image":{"path":"assets/activity.png","caption":"理论学习活动现场"}}
```

必须出现于`heading → figure → paragraph`三块结构；一次只允许一个图块。图名不含“图1”等前缀。图片必须已存在且位于输入JSON目录以内；路径不能绝对定位、`..`越界或软链逃逸；仅PNG/JPEG静态图片，单张不超过20MB及4000万像素。

普通表格：

```json
{
  "type":"table",
  "caption":"材料清单",
  "headers":["名称","份数"],
  "row_header":false,
  "rows":[["学习提纲","1"],["交流材料","1"]]
}
```

表名不含“表1”。所有文字及数字单元格均使用字符串，不能将数字直接填成JSON数值。不得写空单元格；如真实业务内容为“无”，先确认后填“无”，不能为填表编造。

`row_header`是**语义字段而非任意加粗开关**：第一列是否为标题列，应由用户内容明确；不明确时询问。没有标题列就是false；有标题列就是true，但两种情况下都**只有表头行加粗**，首列及以下各行保持常规。它不能用来追求某种视觉效果。

表内图片：

```json
{
  "type":"table",
  "caption":"活动图片记录",
  "headers":["第一组","第二组"],
  "row_header":false,
  "rows":[[
    {"image":{"path":"assets/a.png","caption":"集中学习现场"}},
    {"image":{"path":"assets/b.png","caption":"交流研讨现场"}}
  ]]
}
```

每个图片单元格只有一图及其图注，不能另加正文。标题行不能放图；被认定为标题列的首列不能放图。同表所有图片须同宽高比，否则停止并请用户提供符合尺寸的原图，不能擅自拉伸或裁切。

## 可选段落

```json
"author":"用户已确认的姓名"
```

```json
"signature":{"organization":"用户已确认的落款单位","date":"2026-10-28"}
```

日期是ISO格式的真实有效日期，不能自动使用今天。带落款时，`blocks`最后一项必须是普通正文段；两个空行由程序插入，不在JSON中写空段。

```json
"attachments":[
  {"title":"工作安排表","blocks":[{"type":"paragraph","text":"附件正文内容。"}]}
]
```

附件没有就省略整个字段；存在时至少1个、至多99个，每个新起一页。附件块支持同样的四类内容，不允许嵌套附件。附件标题不带“附件1：”，程序生成。

## 文本限制

标题160字符、姓名/落款单位100字符、普通段落8000字符、表名/图名100字符、列标题60字符、单元格1000字符；每组正文最多2000块。只允许内容本身的单个半角空格。禁止换行、制表符、首尾空白、连续空格、全角空格、控制字符、零宽格式字符、Markdown/HTML排版语法、全角数字或全角字母（数字和字母必须为半角并交Times New Roman）。

长度限制是本skill执行能力边界，不是原PDF对文稿篇幅的规定。超限时不能偷偷删内容；请用户允许合理拆分，或停止。

所有文本都按纯文本转义，不会把用户输入当作XML或代码执行。单元格恰为两个汉字时，由程序执行“名　称”三字宽处理；用户不要预先加空格。

## 字体文件配置

`fonts.json`根对象必须且只能含`title/body/kai/hei/latin`五项，值均为合法TTF/OTF文件的绝对路径。配置路径与文件名本身不证明字体真实身份，程序还检查内部字体名称、字形覆盖并记录SHA256。字体内部名允许命中以下同家族别名，别名不是“近似替代”：

- `title`：`方正小标宋简体`、`FZXiaoBiaoSong-B05S`、`FZXBSJW--GB1-0`、`FZXiaoBiaoSongJianTi`
- `body`：`仿宋_GB2312`、`FangSong_GB2312`、`FZSJ-FANGSGBTTOT`、`FZFSJW--GB1-0`
- `kai`：`楷体_GB2312`、`KaiTi_GB2312`、`FZSJ-KAITGBTTOT`
- `hei`：`黑体`、`SimHei`
- `latin`：`Times New Roman`

TTC字体集合暂不支持，不能改扩展名伪装。

构建主机和实际渲染主机必须真正使用这些字体，不能只有字体名字。运行本skill不授予字体授权；不得提取原PDF中已嵌入的子集字体充当完整字体；不得改名、以思源/Noto/系统仿宋等替代。
