#!/usr/bin/env python3
"""青年新语公文格式：封闭输入、确定性 OOXML、重建比对、失败关闭。"""
import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
import zipfile
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as E

VERSION = '1.0.1'
PROFILE = 'qnxy-explicit-layout-v1'
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
}
for prefix, uri in NS.items():
    E.register_namespace(prefix, uri)
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
FONTS = {'title': '方正小标宋简体', 'body': '仿宋_GB2312', 'kai': '楷体_GB2312',
         'hei': '黑体', 'latin': 'Times New Roman'}
ALIASES = {
    'title': {'方正小标宋简体', 'FZXiaoBiaoSong-B05S', 'FZXBSJW--GB1-0', 'FZXiaoBiaoSongJianTi'},
    'body': {'仿宋_GB2312', 'FangSong_GB2312', 'FZSJ-FANGSGBTTOT', 'FZFSJW--GB1-0'},
    'kai': {'楷体_GB2312', 'KaiTi_GB2312', 'FZSJ-KAITGBTTOT'},
    'hei': {'黑体', 'SimHei'},
    'latin': {'Times New Roman'},
}
# 字号单位为半磅，行距单位为 twip；这些名称不接受调用者覆盖。
ROLES = {
    'title': ('title', 44, 640, 'center', 0, False),
    'author': ('kai', 32, 560, 'center', 0, False),
    'body': ('body', 32, 560, 'both', 200, False),
    'h1': ('hei', 32, 560, 'both', 200, False),
    'h2': ('kai', 32, 560, 'both', 200, False),
    'h3': ('body', 32, 560, 'both', 200, False),
    'h4': ('body', 32, 560, 'both', 200, False),
    'signature': ('body', 32, 560, 'right', 0, False),
    'blank': ('body', 32, 560, 'both', 0, False),
    'attachment': ('body', 32, 560, 'both', 200, False),
    'caption': ('body', 21, 320, 'center', 0, False),
    'cell': ('body', 28, 400, 'center', 0, False),
    'cell_header': ('body', 28, 400, 'center', 0, True),
    'page_odd': ('latin', 28, 400, 'right', 0, False),
    'page_even': ('latin', 28, 400, 'left', 0, False),
}
PAGE_W, PAGE_H = 11906, 16838
MARGIN_X, MARGIN_Y = 1440, 1440
TEXT_W = PAGE_W - 2 * MARGIN_X
MAX_IMAGE_H = 5000


class Invalid(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise Invalid(message)


def keys(obj, required, optional=(), where='对象'):
    need(type(obj) is dict, f'{where}必须为对象')
    need(set(required) <= set(obj), f'{where}缺少字段：{set(required)-set(obj)}')
    need(set(obj) <= set(required) | set(optional), f'{where}含未授权字段：{set(obj)-set(required)-set(optional)}')


def no_duplicates(pairs):
    result = {}
    for k, v in pairs:
        need(k not in result, f'JSON 字段重复：{k}')
        result[k] = v
    return result


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=no_duplicates)


def text(s, where='文本', max_len=8000):
    need(type(s) is str and 0 < len(s) <= max_len, f'{where}必须是非空字符串，最长{max_len}字符')
    need(s == s.strip(), f'{where}禁止首尾空白')
    need('  ' not in s and '\u3000' not in s, f'{where}禁止以连续空格或全角空格排版')
    need(not any(unicodedata.category(c).startswith('C') for c in s), f'{where}禁止控制字符、换行、制表符和不可见格式字符')
    need(not any(unicodedata.category(c) in {'Zl', 'Zp'} for c in s), f'{where}禁止手工换行')
    need(not any(c.isspace() and c != ' ' for c in s), f'{where}只允许单个半角空格')
    need(not re.search(r'(^| )[#>*•●▪]|```|\*\*|__|!\[|\]\(|<[^>]+>', s), f'{where}禁止 Markdown、HTML 或项目符号排版')
    need(not re.search(r'[\uFF10-\uFF19\uFF21-\uFF3A\uFF41-\uFF5A]', s), f'{where}禁止全角数字或字母；数字和字母必须使用半角Times New Roman')
    return s


def relative_asset(base, value):
    text(value, '图片路径', 240)
    p = Path(value)
    need(not p.is_absolute() and '..' not in p.parts, '图片必须为输入目录内相对路径')
    resolved = (base / p).resolve()
    need(resolved.is_relative_to(base.resolve()), '图片路径越界')
    need(resolved.is_file(), f'图片不存在：{value}')
    need(resolved.stat().st_size <= 20_000_000, '单图不能大于20MB')
    return resolved


def image_spec(obj, base):
    from PIL import Image
    keys(obj, ['path', 'caption'], where='图片')
    text(obj['caption'], '图名', 100)
    need(not re.match(r'^图\s*\d', obj['caption']), '图名禁止自带图号')
    path = relative_asset(base, obj['path'])
    with Image.open(path) as im:
        need(im.format in {'PNG', 'JPEG'}, '只允许 PNG/JPEG 图片')
        need(getattr(im, 'n_frames', 1) == 1, '禁止动画图片')
        need(im.width > 0 and im.height > 0 and im.width * im.height <= 40_000_000, '图片尺寸无效或过大')
        im.verify()


def validate_blocks(blocks, base, where):
    need(type(blocks) is list and 0 < len(blocks) <= 2000, f'{where}必须为非空数组，最多2000项')
    last_level = 0
    for i, block in enumerate(blocks):
        need(type(block) is dict, '内容块必须是对象')
        kind = block.get('type')
        if kind == 'paragraph':
            keys(block, ['type', 'text'], where='正文段落')
            text(block['text'])
            need(not re.match(r'^(?:[一二三四五六七八九十百]+、|（[一二三四五六七八九十百]+）|[0-9]+\.|（[0-9]+）)', block['text']), '正文不得冒充带编号标题；请用 heading')
        elif kind == 'heading':
            keys(block, ['type', 'level', 'text'], where='标题')
            level = block['level']
            need(type(level) is int and 1 <= level <= 4, '只允许1至4级标题')
            need(level <= last_level + 1, '标题不得跳级，首个标题必须为一级')
            text(block['text'], '标题', 160)
            need(not re.match(r'^(?:[一二三四五六七八九十百]+、|（[一二三四五六七八九十百]+）|[0-9]+\.|（[0-9]+）)', block['text']), '标题文本不得自带序号')
            need(i + 1 < len(blocks), '标题后不得没有内容')
            last_level = level
        elif kind == 'figure':
            keys(block, ['type', 'image'], where='正文图片')
            image_spec(block['image'], base)
            need(i > 0 and blocks[i-1]['type'] == 'heading', '正文图片必须紧接所属标题')
            need(i + 1 < len(blocks) and blocks[i+1]['type'] == 'paragraph', '正文图片及图注后必须紧接正文段落')
        elif kind == 'table':
            keys(block, ['type', 'caption', 'headers', 'rows', 'row_header'], where='表格')
            text(block['caption'], '表名', 100)
            need(not re.match(r'^表\s*\d', block['caption']), '表名禁止自带表号')
            need(type(block['headers']) is list and 1 <= len(block['headers']) <= 6, '表格必须有1至6列标题')
            for h in block['headers']:
                text(h, '列标题', 60)
            need(type(block['rows']) is list and 0 < len(block['rows']) <= 200, '表格须有1至200行正文')
            need(type(block['row_header']) is bool, 'row_header必须明确为true或false')
            pictures = []
            for row in block['rows']:
                need(type(row) is list and len(row) == len(block['headers']), '表格必须为矩形，禁止合并单元格')
                for col, cell in enumerate(row):
                    if type(cell) is str:
                        text(cell, '单元格', 1000)
                    else:
                        keys(cell, ['image'], where='图片单元格')
                        need(not (block['row_header'] and col == 0), '标题列不允许图片')
                        image_spec(cell['image'], base)
                        from PIL import Image
                        with Image.open(relative_asset(base, cell['image']['path'])) as im:
                            pictures.append((im.width, im.height))
            if pictures:
                w, h = pictures[0]
                need(all(w2 * h == w * h2 for w2, h2 in pictures), '同一表内所有图片宽高比必须一致；禁止拉伸、裁切或加边补齐')
        else:
            raise Invalid(f'未授权内容块：{kind!r}')


def validate_input(data, base):
    keys(data, ['profile', 'approval', 'title', 'blocks'], ['author', 'signature', 'attachments'], '文档')
    need(data['profile'] == PROFILE, '不认识或未批准的排版配置')
    keys(data['approval'], ['confirmed_by', 'confirmation'], where='确认记录')
    text(data['approval']['confirmed_by'], '确认人', 100)
    need(data['approval']['confirmation'] == '已阅读并同意 references/layout-profile.md 的全部补充规则', '必须先取得用户真实确认，禁止伪造确认记录')
    text(data['title'], '文档标题', 160)
    if 'author' in data:
        text(data['author'], '个人名称', 100)
    validate_blocks(data['blocks'], base, '正文')
    need(any(x['type'] == 'paragraph' for x in data['blocks']), '正文必须至少有一个正文段落')
    if 'signature' in data:
        s = data['signature']
        keys(s, ['organization', 'date'], where='落款')
        text(s['organization'], '落款单位', 100)
        need(re.fullmatch(r'\d{4}-\d{2}-\d{2}', s['date'] or '') is not None, '日期必须为YYYY-MM-DD')
        date.fromisoformat(s['date'])
        need(data['blocks'][-1]['type'] == 'paragraph', '有落款时正文必须以正文段落结束')
    if 'attachments' in data:
        need(type(data['attachments']) is list and 0 < len(data['attachments']) <= 99, '附件数组不能空，最多99项')
        for item in data['attachments']:
            keys(item, ['title', 'blocks'], where='附件')
            text(item['title'], '附件名', 160)
            validate_blocks(item['blocks'], base, '附件正文')
    return data


def font_role(c, role):
    # 汉字不是此处“字母”；所有 Unicode 数字及非 CJK 字母交由西文字体。
    cat = unicodedata.category(c)
    name = unicodedata.name(c, '')
    latin = cat.startswith('N') or (cat.startswith('L') and not any(x in name for x in ('CJK', 'IDEOGRAPH', 'HIRAGANA', 'KATAKANA', 'HANGUL')))
    return 'latin' if latin else role


def font_check(config_path, data):
    from fontTools.ttLib import TTFont
    cfg = load_json(config_path)
    keys(cfg, list(FONTS), where='字体配置')
    report, cmaps = {}, {}
    for role, file in cfg.items():
        need(type(file) is str, '字体文件路径必须为字符串')
        path = Path(file)
        need(path.is_absolute() and path.is_file() and path.suffix.lower() in {'.ttf', '.otf'}, f'缺少字体绝对路径，或字体文件格式不是TTF/OTF：{role}')
        ft = TTFont(path)
        records = [(n.nameID, n.toUnicode()) for n in ft['name'].names if n.nameID in {1, 4, 6, 16}]
        names = {value for _, value in records}
        matched = None
        for name_id in (1, 16):
            for record_id, value in records:
                if record_id == name_id and value in ALIASES[role]:
                    matched = value
                    break
            if matched:
                break
        need(matched is not None, f'{role}字体缺少允许的家族名（family/typographic family）：{sorted(names)}；禁止近似替代')
        # DOCX 必须写入字体文件中真实存在的family名，不能只写一个fontconfig别名。
        FONTS[role] = matched
        cmaps[role] = set((ft.getBestCmap() or {}).keys())
        report[role] = {'family': matched, 'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        ft.close()
    for role, s in required_texts(data):
        for c in s:
            if c == ' ':
                continue
            selected = font_role(c, role)
            need(ord(c) in cmaps[selected], f'指定字体缺少字形：{selected} / {c!r} U+{ord(c):04X}；禁止字体回退')
    return report


def required_texts(data):
    yield 'title', data['title']
    if 'author' in data:
        yield 'kai', data['author']
    yield 'body', '附件：表图一二三四五六七八九十百、（）年月日.\u3000'
    yield 'hei', '一二三四五六七八九十、'
    yield 'kai', '一二三四五六七八九十（）'
    yield 'latin', '0123456789—'
    if 'signature' in data:
        yield 'body', data['signature']['organization']
    groups = [data['blocks']] + [a['blocks'] for a in data.get('attachments', [])]
    for a in data.get('attachments', []):
        yield 'body', a['title']
    for blocks in groups:
        for b in blocks:
            kind = b['type']
            if kind in {'heading', 'paragraph'}:
                yield ('hei' if b.get('level') == 1 else 'kai' if b.get('level') == 2 else 'body'), b['text']
            if kind == 'figure':
                yield 'body', b['image']['caption']
            if kind == 'table':
                yield 'body', b['caption']
                for h in b['headers']:
                    yield 'body', h
                for row in b['rows']:
                    for c in row:
                        yield 'body', c if type(c) is str else c['image']['caption']


def tag(name):
    p, n = name.split(':')
    return '{' + NS[p] + '}' + n


def el(name, attrs=None, value=None):
    a = {(tag(k) if ':' in k else k): str(v) for k, v in (attrs or {}).items()}
    e = E.Element(tag(name), a)
    if value is not None:
        e.text = str(value)
    return e


def sub(parent, name, attrs=None, value=None):
    child = el(name, attrs, value)
    parent.append(child)
    return child


def xml(root):
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def run_properties(role, size, bold=False):
    p = el('w:rPr')
    sub(p, 'w:rFonts', {'w:ascii': FONTS['latin'], 'w:hAnsi': FONTS['latin'], 'w:eastAsia': FONTS[role], 'w:cs': FONTS['latin'], 'w:hint': 'default' if role == 'latin' else 'eastAsia'})
    sub(p, 'w:b', {'w:val': '1' if bold else '0'})
    sub(p, 'w:bCs', {'w:val': '1' if bold else '0'})
    sub(p, 'w:i', {'w:val': '0'})
    sub(p, 'w:color', {'w:val': '000000'})
    sub(p, 'w:spacing', {'w:val': '0'})
    sub(p, 'w:w', {'w:val': '100'})
    sub(p, 'w:sz', {'w:val': size})
    sub(p, 'w:szCs', {'w:val': size})
    sub(p, 'w:u', {'w:val': 'none'})
    sub(p, 'w:vertAlign', {'w:val': 'baseline'})
    sub(p, 'w:lang', {'w:val': 'en-US', 'w:eastAsia': 'zh-CN'})
    return p


def add_text(p, value, role, size, bold=False):
    if not value:
        return
    segments = []
    for c in value:
        selected = font_role(c, role)
        if segments and segments[-1][0] == selected:
            segments[-1][1] += c
        else:
            segments.append([selected, c])
    for selected, s in segments:
        r = sub(p, 'w:r')
        r.append(run_properties(selected, size, bold))
        t = sub(r, 'w:t', value=s)
        if s.startswith(' ') or s.endswith(' '):
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')


def paragraph(value, role, keep=False, page_break=False, line_override=None):
    font, size, line, align, indent, bold = ROLES[role]
    p = el('w:p')
    pp = sub(p, 'w:pPr')
    sub(pp, 'w:keepNext', {'w:val': '1' if keep else '0'})
    sub(pp, 'w:keepLines', {'w:val': '1' if role != 'body' else '0'})
    sub(pp, 'w:pageBreakBefore', {'w:val': '1' if page_break else '0'})
    sub(pp, 'w:widowControl', {'w:val': '1'})
    sub(pp, 'w:autoSpaceDE', {'w:val': '0'})
    sub(pp, 'w:autoSpaceDN', {'w:val': '0'})
    sub(pp, 'w:snapToGrid', {'w:val': '0'})
    sub(pp, 'w:spacing', {'w:before': '0', 'w:after': '0', 'w:line': line_override or line, 'w:lineRule': 'exact', 'w:beforeAutospacing': '0', 'w:afterAutospacing': '0'})
    ind = {'w:left': '0', 'w:right': '0', 'w:firstLine': str(size * 20 if indent else 0), 'w:firstLineChars': str(indent)}
    if role == 'page_odd':
        ind['w:right'] = '280'
    if role == 'page_even':
        ind['w:left'] = '280'
    sub(pp, 'w:ind', ind)
    sub(pp, 'w:jc', {'w:val': align})
    if role in {'h1', 'h2', 'h3', 'h4'}:
        sub(pp, 'w:outlineLvl', {'w:val': str(int(role[-1])-1)})
    pp.append(run_properties(font, size, bold))
    add_text(p, value, font, size, bold)
    return p


def chinese_number(n):
    need(1 <= n <= 99, '每个标题层级在同一父级下最多99项')
    c = '零一二三四五六七八九'
    if n < 10:
        return c[n]
    return (c[n//10] if n >= 20 else '') + '十' + (c[n%10] if n%10 else '')


def heading_label(level, n):
    return {1: lambda: chinese_number(n)+'、', 2: lambda: '（'+chinese_number(n)+'）', 3: lambda: str(n)+'.', 4: lambda: '（'+str(n)+'）'}[level]()


def package_relationships(items):
    root = E.Element('Relationships', {'xmlns': REL})
    for ident, kind, target in items:
        E.SubElement(root, 'Relationship', {'Id': ident, 'Type': NS['r']+'/'+kind, 'Target': target})
    return xml(root)


class Builder:
    def __init__(self, data, base):
        self.data, self.base = data, base
        self.parts = {}
        self.rels = [('rStyles', 'styles', 'styles.xml'), ('rSettings', 'settings', 'settings.xml'), ('rOdd', 'footer', 'footer1.xml'), ('rEven', 'footer', 'footer2.xml')]
        self.fig_no, self.table_no, self.pic_id = 0, 0, 0
        self.document = el('w:document')
        self.body = sub(self.document, 'w:body')

    def image_geometry(self, image, max_width):
        from PIL import Image
        with Image.open(relative_asset(self.base, image['path'])) as im:
            w, h = im.size
        width = min(max_width, 7200)
        height = round(width * h / w)
        if height > MAX_IMAGE_H:
            width = round(width * MAX_IMAGE_H / height)
            height = MAX_IMAGE_H
        return width, height

    def picture(self, image, width, height, floating):
        self.pic_id += 1
        num = self.pic_id
        path = relative_asset(self.base, image['path'])
        from PIL import Image
        with Image.open(path) as im:
            ext = 'png' if im.format == 'PNG' else 'jpg'
        media = f'media/image{num}.{ext}'
        self.parts['word/'+media] = path.read_bytes()
        self.rels.append((f'rImage{num}', 'image', media))
        # 图片自身撑开布局；再预留一个图片高度会产生双倍空白或裁切。
        p = paragraph('', 'caption', keep=True, line_override=20)
        pp = p.find('w:pPr', NS)
        pp.remove(pp.find('w:rPr', NS))
        pp.append(run_properties('body', 2))
        if not floating:
            spacing = pp.find('w:spacing', NS)
            spacing.set(tag('w:line'), '240')
            spacing.set(tag('w:lineRule'), 'auto')
        r = sub(p, 'w:r')
        r.append(run_properties('body', 2))
        drawing = sub(r, 'w:drawing')
        cx, cy = width * 635, height * 635
        if floating:
            box = sub(drawing, 'wp:anchor', {'distT': '0', 'distB': '0', 'distL': '0', 'distR': '0', 'simplePos': '0', 'relativeHeight': '0', 'behindDoc': '0', 'locked': '0', 'layoutInCell': '1', 'allowOverlap': '0'})
            sub(box, 'wp:simplePos', {'x': '0', 'y': '0'})
            hp = sub(box, 'wp:positionH', {'relativeFrom': 'column'})
            sub(hp, 'wp:align', value='center')
            vp = sub(box, 'wp:positionV', {'relativeFrom': 'paragraph'})
            sub(vp, 'wp:posOffset', value='0')
        else:
            box = sub(drawing, 'wp:inline', {'distT': '0', 'distB': '0', 'distL': '0', 'distR': '0'})
        sub(box, 'wp:extent', {'cx': cx, 'cy': cy})
        sub(box, 'wp:effectExtent', {'l': '0', 't': '0', 'r': '0', 'b': '0'})
        if floating:
            sub(box, 'wp:wrapTopAndBottom')
        sub(box, 'wp:docPr', {'id': num, 'name': f'Image{num}', 'descr': image['caption']})
        locks = sub(box, 'wp:cNvGraphicFramePr')
        sub(locks, 'a:graphicFrameLocks', {'noChangeAspect': '1'})
        g = sub(box, 'a:graphic')
        gd = sub(g, 'a:graphicData', {'uri': NS['pic']})
        pic = sub(gd, 'pic:pic')
        nv = sub(pic, 'pic:nvPicPr')
        sub(nv, 'pic:cNvPr', {'id': num, 'name': f'Image{num}'})
        sub(nv, 'pic:cNvPicPr')
        fill = sub(pic, 'pic:blipFill')
        sub(fill, 'a:blip', {'r:embed': f'rImage{num}'})
        stretch = sub(fill, 'a:stretch')
        sub(stretch, 'a:fillRect')
        sp = sub(pic, 'pic:spPr')
        xfrm = sub(sp, 'a:xfrm')
        sub(xfrm, 'a:off', {'x': '0', 'y': '0'})
        sub(xfrm, 'a:ext', {'cx': cx, 'cy': cy})
        geom = sub(sp, 'a:prstGeom', {'prst': 'rect'})
        sub(geom, 'a:avLst')
        return p

    def table(self, block):
        self.table_no += 1
        self.body.append(paragraph(f'表{self.table_no} '+block['caption'], 'caption', keep=True))
        table = sub(self.body, 'w:tbl')
        pr = sub(table, 'w:tblPr')
        sub(pr, 'w:tblW', {'w:w': TEXT_W, 'w:type': 'dxa'})
        sub(pr, 'w:jc', {'w:val': 'center'})
        sub(pr, 'w:tblInd', {'w:w': '0', 'w:type': 'dxa'})
        borders = sub(pr, 'w:tblBorders')
        for side in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            sub(borders, 'w:'+side, {'w:val': 'single', 'w:sz': '2', 'w:space': '0', 'w:color': '000000'})
        sub(pr, 'w:tblLayout', {'w:type': 'fixed'})
        margins = sub(pr, 'w:tblCellMar')
        for side in ['top', 'left', 'bottom', 'right']:
            sub(margins, 'w:'+side, {'w:w': '80', 'w:type': 'dxa'})
        columns = len(block['headers'])
        widths = [TEXT_W // columns] * columns
        widths[-1] += TEXT_W - sum(widths)
        grid = sub(table, 'w:tblGrid')
        for width in widths:
            sub(grid, 'w:gridCol', {'w:w': width})
        local_fig = 0
        for row_idx, row in enumerate([block['headers']] + block['rows']):
            tr = sub(table, 'w:tr')
            trpr = sub(tr, 'w:trPr')
            sub(trpr, 'w:cantSplit')
            if row_idx == 0:
                sub(trpr, 'w:tblHeader')
            images = [c['image'] for c in row if type(c) is dict]
            dimensions = self.image_geometry(images[0], min(widths)-160) if images else None
            for col, cell in enumerate(row):
                tc = sub(tr, 'w:tc')
                tcpr = sub(tc, 'w:tcPr')
                sub(tcpr, 'w:tcW', {'w:w': widths[col], 'w:type': 'dxa'})
                sub(tcpr, 'w:vAlign', {'w:val': 'center'})
                if type(cell) is str:
                    if (row_idx == 0 or (block['row_header'] and col == 0)) and re.fullmatch(r'[\u3400-\u9fff]{2}', cell):
                        cell = cell[0]+'\u3000'+cell[1]
                    role = 'cell_header' if row_idx == 0 else 'cell'
                    tc.append(paragraph(cell, role))
                else:
                    local_fig += 1
                    tc.append(self.picture(cell['image'], *dimensions, floating=False))
                    tc.append(paragraph(f'图{local_fig} '+cell['image']['caption'], 'caption'))

    def blocks(self, blocks):
        counters = [0, 0, 0, 0]
        for block in blocks:
            kind = block['type']
            if kind == 'paragraph':
                self.body.append(paragraph(block['text'], 'body'))
            elif kind == 'heading':
                level = block['level']
                counters[level-1] += 1
                need(counters[level-1] <= 99, '同父级标题数量超过99')
                counters[level:] = [0] * (4-level)
                value = heading_label(level, counters[level-1]) + block['text']
                self.body.append(paragraph(value, 'h'+str(level), keep=True))
            elif kind == 'figure':
                self.fig_no += 1
                image = block['image']
                self.body.append(self.picture(image, *self.image_geometry(image, TEXT_W), floating=True))
                self.body.append(paragraph(f'图{self.fig_no} '+image['caption'], 'caption', keep=True))
            elif kind == 'table':
                self.table(block)

    def footer(self, even):
        root = el('w:ftr')
        p = paragraph('— ', 'page_even' if even else 'page_odd')
        field = sub(p, 'w:fldSimple', {'w:instr': ' PAGE ', 'w:dirty': 'true'})
        add_text(field, '2' if even else '1', 'latin', 28)
        add_text(p, ' —', 'latin', 28)
        root.append(p)
        return xml(root)

    def build(self):
        d = self.data
        self.body.append(paragraph(d['title'], 'title', keep=True))
        if 'author' in d:
            self.body.append(paragraph(d['author'], 'author', keep=True))
        self.blocks(d['blocks'])
        if 'signature' in d:
            # 保持正文最后段、两个真实空行和完整落款同页。
            last = self.body[-1].find('w:pPr/w:keepNext', NS)
            last.set(tag('w:val'), '1')
            self.body.append(paragraph('', 'blank', keep=True))
            self.body.append(paragraph('', 'blank', keep=True))
            self.body.append(paragraph(d['signature']['organization'], 'signature', keep=True))
            y, m, day = map(int, d['signature']['date'].split('-'))
            self.body.append(paragraph(f'{y}年{m}月{day}日', 'signature'))
        for n, attachment in enumerate(d.get('attachments', []), 1):
            self.body.append(paragraph(f'附件{n}：'+attachment['title'], 'attachment', keep=True, page_break=True))
            self.blocks(attachment['blocks'])
        sect = sub(self.body, 'w:sectPr')
        sub(sect, 'w:footerReference', {'w:type': 'default', 'r:id': 'rOdd'})
        sub(sect, 'w:footerReference', {'w:type': 'even', 'r:id': 'rEven'})
        sub(sect, 'w:pgSz', {'w:w': PAGE_W, 'w:h': PAGE_H, 'w:orient': 'portrait'})
        sub(sect, 'w:pgMar', {'w:top': MARGIN_Y, 'w:right': MARGIN_X, 'w:bottom': MARGIN_Y, 'w:left': MARGIN_X, 'w:header': '0', 'w:footer': '720', 'w:gutter': '0'})
        sub(sect, 'w:pgNumType', {'w:fmt': 'decimal', 'w:start': '1'})
        sub(sect, 'w:cols', {'w:num': '1', 'w:space': '0'})
        sub(sect, 'w:docGrid', {'w:type': 'default'})
        self.parts['word/document.xml'] = xml(self.document)
        self.parts['word/footer1.xml'] = self.footer(False)
        self.parts['word/footer2.xml'] = self.footer(True)
        styles = el('w:styles')
        defaults = sub(styles, 'w:docDefaults')
        rd = sub(defaults, 'w:rPrDefault')
        rd.append(run_properties('body', 32))
        pd = sub(defaults, 'w:pPrDefault')
        default_p = copy.deepcopy(paragraph('', 'body').find('w:pPr', NS))
        default_p.remove(default_p.find('w:rPr', NS))
        pd.append(default_p)
        normal = sub(styles, 'w:style', {'w:type': 'paragraph', 'w:default': '1', 'w:styleId': 'Normal'})
        sub(normal, 'w:name', {'w:val': 'Normal'})
        self.parts['word/styles.xml'] = xml(styles)
        settings = el('w:settings')
        sub(settings, 'w:defaultTabStop', {'w:val': '420'})
        sub(settings, 'w:evenAndOddHeaders')
        sub(settings, 'w:characterSpacingControl', {'w:val': 'doNotCompress'})
        sub(settings, 'w:updateFields', {'w:val': 'true'})
        compat = sub(settings, 'w:compat')
        sub(compat, 'w:compatSetting', {'w:name': 'compatibilityMode', 'w:uri': 'http://schemas.microsoft.com/office/word', 'w:val': '15'})
        self.parts['word/settings.xml'] = xml(settings)
        self.parts['_rels/.rels'] = package_relationships([('rDocument', 'officeDocument', 'word/document.xml')])
        self.parts['word/_rels/document.xml.rels'] = package_relationships(self.rels)
        content = E.Element('Types', {'xmlns': CT})
        for ext, mime in [('rels', 'application/vnd.openxmlformats-package.relationships+xml'), ('xml', 'application/xml'), ('png', 'image/png'), ('jpg', 'image/jpeg')]:
            E.SubElement(content, 'Default', {'Extension': ext, 'ContentType': mime})
        for part, kind in [('document', 'document.main'), ('styles', 'styles'), ('settings', 'settings'), ('footer1', 'footer'), ('footer2', 'footer')]:
            E.SubElement(content, 'Override', {'PartName': '/word/'+part+'.xml', 'ContentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.'+kind+'+xml'})
        self.parts['[Content_Types].xml'] = xml(content)
        return self.parts


def write_package(parts, path):
    path = Path(path)
    need(not path.exists(), f'输出已存在，拒绝覆盖：{path}')
    need(path.parent.is_dir(), '输出目录不存在，请先建立目录')
    with path.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, content in sorted(parts.items()):
                zi = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, content)


def check_package(path, expected):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        need(len(names) == len(set(names)), 'DOCX含重复ZIP条目')
        need(set(names) == set(expected), 'DOCX包部件白名单不匹配，可能含未授权格式、宏、链接或附件')
        for n in names:
            need(z.getinfo(n).file_size == len(expected[n]), f'{n}大小不匹配；必须从原始输入重新生成')
            actual = z.read(n)
            need(actual == expected[n], f'{n}与确定性规范不一致；禁止手工修补、样式覆盖或忽略错误')
    return {'structure': 'PASS', 'parts': len(expected), 'docx_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def save_json(path, obj):
    p = Path(path)
    need(not p.exists(), f'拒绝覆盖：{p}')
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def doctor():
    import importlib.util
    missing = [m for m in ['PIL', 'fontTools'] if importlib.util.find_spec(m) is None]
    need(not missing, '缺少依赖：'+', '.join(missing))
    print(json.dumps({'python': sys.version.split()[0], 'script_version': VERSION, 'dependencies': 'PASS', 'note': 'doctor不代表字体、结构或版面验收通过'}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='cmd', required=True)
    subparsers.add_parser('doctor')
    for cmd in ('check-input', 'font-check', 'build', 'validate'):
        p = subparsers.add_parser(cmd)
        p.add_argument('--input', required=True)
        if cmd in {'font-check', 'build', 'validate'}:
            p.add_argument('--fonts', required=True)
        if cmd == 'build':
            p.add_argument('--output', required=True)
        if cmd == 'validate':
            p.add_argument('--docx', required=True)
        if cmd in {'build', 'validate'}:
            p.add_argument('--report', required=True)
    args = parser.parse_args()
    try:
        need(sys.version_info >= (3, 10), '需要Python 3.10以上')
        if args.cmd == 'doctor':
            doctor()
            return 0
        inp = Path(args.input).resolve()
        data = validate_input(load_json(inp), inp.parent)
        if args.cmd == 'check-input':
            print('INPUT PASS（仅内容结构通过，不代表文件验收）')
            return 0
        fonts = font_check(args.fonts, data)
        if args.cmd == 'font-check':
            print(json.dumps({'font_files': 'PASS', 'fonts': fonts, 'note': '还须在实际渲染主机安装并核对这些原字体'}, ensure_ascii=False, indent=2))
            return 0
        parts = Builder(data, inp.parent).build()
        need(not Path(args.report).exists(), '报告已存在，拒绝覆盖')
        if args.cmd == 'build':
            need(Path(args.output).suffix.lower() == '.docx', '输出扩展名必须为.docx')
            write_package(parts, args.output)
            path = args.output
        else:
            path = args.docx
        result = check_package(path, parts)
        result.update({'version': VERSION, 'profile': PROFILE, 'input_sha256': hashlib.sha256(inp.read_bytes()).hexdigest(), 'fonts': fonts,
                       'release_status': 'BLOCKED_PENDING_VISUAL_REVIEW', 'note': '字体文件和OOXML结构通过；还必须核对实际字体使用、更新页码域并逐页人工验收，不得直接声称完全合格。'})
        save_json(args.report, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (Invalid, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ImportError) as exc:
        print('BLOCKED: '+str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
