#!/usr/bin/env python3
"""渲染门禁和逐页验收凭据。不得用验收JSON代替真实逐页审阅。"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import qnxy as q

CHECKS = ['fonts_and_sizes', 'line_spacing_and_indents', 'no_clipping_or_overlap',
          'headings_and_captions_stay_with_content', 'table_borders_and_cells',
          'image_placement_and_proportions', 'signature_two_blank_lines',
          'attachment_starts_new_page', 'odd_even_page_number']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize_font(name):
    name = name.lstrip('/')
    name = re.sub(r'^[A-Z]{6}\+', '', name)
    name = re.sub(r'[\s_\-]', '', name).lower()
    # 只剥离渲染器/字体包常见的字面与变体后缀，保留字号族主体。
    suffixes = ('bolditalicmt', 'vkana', 'boldmt', 'italicmt', 'psmt',
                'regular', 'bold', 'italic', 'ps', 'mt')
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if name.endswith(suffix) and len(name) > len(suffix):
                name = name[:-len(suffix)]
                changed = True
                break
    return name


def expected_font_names(fonts):
    from fontTools.ttLib import TTFont
    names = set()
    latin = set()
    for role, info in fonts.items():
        ft = TTFont(info['path'])
        base = {normalize_font(n.toUnicode()) for n in ft['name'].names if n.nameID in {1, 4, 6, 16}}
        base |= {normalize_font(n) for n in q.ALIASES[role]}
        ft.close()
        expanded = set(base)
        if role == 'latin':
            expanded.add('timesnewroman')
            latin |= expanded
        names |= expanded
    return names, latin


def audit_pdf(pdf, fonts):
    import pdfplumber
    from pypdf import PdfReader
    allowed_fonts, latin_fonts = expected_font_names(fonts)
    reader = PdfReader(pdf)
    q.need(1 <= len(reader.pages) <= 300, 'PDF页数必须为1至300')
    for page in reader.pages:
        resources = page.get('/Resources', {})
        for ref in resources.get('/Font', {}).values():
            font = ref.get_object()
            children = font.get('/DescendantFonts', [font])
            for child in children:
                item = child.get_object()
                desc = item.get('/FontDescriptor')
                q.need(desc is not None, 'PDF存在未嵌入或无法识别的字体')
                desc = desc.get_object()
                q.need(any(x in desc for x in ['/FontFile', '/FontFile2', '/FontFile3']), 'PDF字体未嵌入')
                name = normalize_font(str(desc.get('/FontName', '')))
                q.need(name in allowed_fonts, f'PDF出现未授权字体：{name}')
    page_results = []
    with pdfplumber.open(pdf) as document:
        for number, page in enumerate(document.pages, 1):
            q.need(abs(page.width - q.PAGE_W/20) < 1 and abs(page.height - q.PAGE_H/20) < 1, 'PDF不是批准的A4纵向尺寸')
            foot = [c for c in page.chars if c['top'] > page.height - 66]
            foot.sort(key=lambda c: (round(c['top']/4), c['x0']))
            label = ''.join(c['text'] for c in foot).replace(' ', '')
            q.need(label == f'—{number}—', f'第{number}页页码不正确或页脚中出现其他内容：{label!r}')
            nonspaces = [c for c in foot if c['text'].strip()]
            q.need(all(abs(c['size']-14) < 0.3 for c in nonspaces), '页码必须四号14pt')
            q.need(all(normalize_font(c['fontname']) in latin_fonts for c in nonspaces), '页码必须Times New Roman')
            edge = max(c['x1'] for c in nonspaces) if number % 2 else min(c['x0'] for c in nonspaces)
            target = page.width - 72 - 14 if number % 2 else 72 + 14
            q.need(abs(edge-target) <= 3, f'第{number}页页码未按奇右偶左空一字定位')
            for c in page.chars:
                q.need(c['x0'] >= -0.5 and c['x1'] <= page.width+0.5 and c['top'] >= -0.5 and c['bottom'] <= page.height+0.5, f'第{number}页有文字超出页面')
                if re.search(r'[A-Za-z0-9]', c['text']):
                    q.need(normalize_font(c['fontname']) in latin_fonts, f'第{number}页数字/字母发生字体回退')
            page_results.append({'page': number, 'automated_pdf_checks': 'PASS'})
    return page_results


def render(args):
    inp = Path(args.input).resolve()
    data = q.validate_input(q.load_json(inp), inp.parent)
    fonts = q.font_check(args.fonts, data)
    q.check_package(args.docx, q.Builder(data, inp.parent).build())
    for executable in ['fc-match', 'soffice', 'pdftoppm']:
        q.need(shutil.which(executable) is not None, f'缺少{executable}；禁止跳过渲染门禁')
    for role, info in fonts.items():
        matched = False
        for candidate in sorted(q.ALIASES[role]):
            p = subprocess.run(['fc-match', '-f', '%{file}', candidate], capture_output=True, text=True, check=True, timeout=20)
            resolved = Path(p.stdout.strip())
            if resolved.is_file() and digest(resolved) == info['sha256']:
                matched = True
                break
        q.need(matched, f'渲染主机未真正使用指定字体：{role}；请依法安装原字体后重新运行')
    out = Path(args.outdir).resolve()
    q.need(not out.exists(), '渲染输出目录必须为尚不存在的新目录')
    q.need(out.parent.is_dir(), '渲染输出父目录不存在')
    out.mkdir()
    with tempfile.TemporaryDirectory(prefix='qnxy-office-') as profile:
        subprocess.run(['soffice', '-env:UserInstallation='+Path(profile).as_uri(), '--headless', '--convert-to', 'pdf:writer_pdf_Export', '--outdir', str(out), str(Path(args.docx).resolve())], check=True, capture_output=True, text=True, timeout=240)
    pdf = out / (Path(args.docx).stem+'.pdf')
    q.need(pdf.is_file() and pdf.stat().st_size > 0, '渲染没有产生有效PDF')
    pages = audit_pdf(pdf, fonts)
    subprocess.run(['pdftoppm', '-r', '120', '-png', str(pdf), str(out/'page')], check=True, capture_output=True, timeout=240)
    screenshots = sorted(out.glob('page-*.png'))
    q.need(len(screenshots) == len(pages), '逐页截图不齐全')
    audit = {'docx_sha256': digest(args.docx), 'pdf_sha256': digest(pdf), 'pages': pages,
             'screenshots': {p.name: digest(p) for p in screenshots}, 'font_files': fonts,
             'status': 'BLOCKED_PENDING_VISUAL_REVIEW'}
    q.save_json(out/'render-audit.json', audit)
    review = {'reviewer': '', 'docx_sha256': audit['docx_sha256'], 'pdf_sha256': audit['pdf_sha256'],
              'pages': [{'page': p['page'], **{k: False for k in CHECKS}} for p in pages]}
    q.save_json(out/'review-to-fill.json', review)
    print('渲染及自动检查通过。必须逐页打开截图，实际审阅后填写review-to-fill.json；当前禁止发布。')


def accept(args):
    inp = Path(args.input).resolve()
    data = q.validate_input(q.load_json(inp), inp.parent)
    fonts = q.font_check(args.fonts, data)
    q.check_package(args.docx, q.Builder(data, inp.parent).build())
    audit = q.load_json(args.audit)
    review = q.load_json(args.review)
    pages = audit_pdf(args.pdf, fonts)
    q.keys(review, ['reviewer', 'docx_sha256', 'pdf_sha256', 'pages'], where='逐页复核')
    q.text(review['reviewer'], '实际审阅者', 100)
    for key, file in [('docx_sha256', args.docx), ('pdf_sha256', args.pdf)]:
        q.need(review[key] == audit[key] == digest(file), '复核记录与当前文件不匹配')
    q.need(audit.get('font_files') == fonts, '验收记录中的字体与当前字体文件不一致')
    q.need(audit['pages'] == pages and audit['status'] == 'BLOCKED_PENDING_VISUAL_REVIEW', '渲染审计记录无效')
    q.need(type(review['pages']) is list and len(review['pages']) == len(pages), '逐页复核不齐全')
    q.need(len(audit['screenshots']) == len(pages), '截图审计不齐全')
    for name, value in audit['screenshots'].items():
        q.need(re.fullmatch(r'page-\d+\.png', name) is not None, '截图文件名无效')
        q.need(digest(Path(args.audit).parent/name) == value, '截图不存在或在审计后被修改')
    for n, page in enumerate(review['pages'], 1):
        q.keys(page, ['page']+CHECKS, where='页复核')
        q.need(type(page['page']) is int and page['page'] == n, '复核页号不连续')
        q.need(all(page[k] is True for k in CHECKS), f'第{n}页仍有未完成或未通过项')
    q.save_json(args.output, {'status': 'RELEASED_WITH_RECORDED_VISUAL_REVIEW',
                            'reviewer': review['reviewer'], 'docx_sha256': digest(args.docx),
                            'pdf_sha256': digest(args.pdf), 'pages': len(pages),
                            'review_record_sha256': digest(args.review),
                            'limit': '程序验证证据完整性，不证明审阅者确实查看过每一页。不得伪造人工或视觉审阅。'})
    print('验收门禁通过；请交付DOCX、PDF及验收凭据。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='cmd', required=True)
    for cmd in ['render', 'accept']:
        p = commands.add_parser(cmd)
        for flag in ['input', 'fonts', 'docx']:
            p.add_argument('--'+flag, required=True)
        if cmd == 'render':
            p.add_argument('--outdir', required=True)
        else:
            for flag in ['pdf', 'audit', 'review', 'output']:
                p.add_argument('--'+flag, required=True)
    args = parser.parse_args()
    try:
        render(args) if args.cmd == 'render' else accept(args)
        return 0
    except (q.Invalid, OSError, ValueError, TypeError, KeyError, ImportError, subprocess.SubprocessError) as exc:
        print('BLOCKED: '+str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
