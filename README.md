# 青年新语公文格式（qingnian-xinyu-gongwen）

四川师范大学“青年新语”大学生理论宣讲团公文格式的生成与审查技能。给定结构化内容后，通过固定生成器与多重门禁产出确定性 `.docx`，不依赖模型“手感”排版。

## 它能做什么

- 按 PDF 原始格式依据（P01—P20）生成规范公文：标题、作者、正文、四级标题、表格、图片、落款、附件、双面页码。
- 对已有 `.docx` 做结构复核：逐字节比对，拒绝手改、样式注入、宏、超链接、额外媒体。
- 渲染后自动检查 PDF 字体嵌入、A4、页码连续性与奇偶位置、文字越界。

## 它不做什么

普通 Word 排版、简历、论文、PPT、一般报告，或任何“把公文排得好看点”的需求。不生成封面、目录、红头、发文字号、印章、水印。

## 安装

作为技能使用时，把整个仓库放进技能目录，例如：

```bash
git clone https://github.com/<you>/qingnian-xinyu-gongwen.git \
  ~/.agent/skills/qingnian-xinyu-gongwen
cd ~/.agent/skills/qingnian-xinyu-gongwen
python -m pip install -r requirements.txt
python scripts/qnxy.py doctor
```

渲染门禁还需要 `fc-match`、`soffice`（LibreOffice）、`pdftoppm`（Poppler）。

## 快速开始

```bash
# 1. 校验内容结构
python scripts/qnxy.py check-input --input work/content.json

# 2. 用随包字体生成 work/fonts.json 并校验字体
python scripts/setup_fonts.py

# 3. 生成 DOCX
python scripts/qnxy.py build --input work/content.json --fonts work/fonts.json \
  --output work/青年新语公文.docx --report work/build-report.json

# 4. 渲染 + 自动检查 + 逐页截图
python scripts/release.py render --input work/content.json --fonts work/fonts.json \
  --docx work/青年新语公文.docx --outdir work/rendered
```

完整流程、九项逐页复核与验收凭据见 `SKILL.md`。

## 目录

| 路径 | 说明 |
|---|---|
| `SKILL.md` | 技能主文档：使用场景、绝对规则、执行流程、P01—P20、禁止格式 |
| `references/source.pdf` | 唯一格式依据（3 页） |
| `references/source-rules.md` | P01—P20 逐条原文、单位换算、执行代码 |
| `references/layout-profile.md` | PDF 未明确、须用户确认的补充参数 |
| `references/input-contract.md` | JSON 输入契约 |
| `scripts/qnxy.py` | 生成器、输入校验、字体检查、结构校验 |
| `scripts/release.py` | 渲染门禁、PDF 自动检查、验收凭据 |
| `assets/fonts/` | 五款原字体及哈希清单 |
| `tests/test_rules.py` | 24 项正反向自动测试 |

## 关键约束

- 白名单封闭：技能未声明允许的格式一律不出现。
- 一个文档一个格式：不混入其他学校或其他年度的参数。
- 不得近似替代字体，不得用 Noto/思源/系统仿宋冒充。
- 表格只有表头行加粗，其余行一律常规。
- 程序通过不等于视觉合格，必须完成逐页人工复核。

## 字体与授权

`assets/fonts/` 中的五款字体（方正小标宋简体、仿宋_GB2312、楷体_GB2312、黑体、Times New Roman）来自高校公开发布的办公字体包，仅作公文排版使用。来源页面说明部分字体仅供非商业用途，商业用途需自行向字体厂商取得授权。本仓库不对这些字体授予任何额外权利，详见 `assets/fonts/README.md` 与 `NOTICE.md`。

## 许可

本仓库代码与文档以 MIT 许可发布；`assets/fonts/` 下的字体文件不在该许可范围内。

## 测试

```bash
python -m unittest discover -s tests -v
```

预期 24 项全部通过。测试中的审批字段是测试夹具，不是任何人的授权。
