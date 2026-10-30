import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import qnxy as q


def fixture():
    return {
        'profile': q.PROFILE,
        'approval': {'confirmed_by': '仅单元测试，不是用户批准', 'confirmation': '已阅读并同意 references/layout-profile.md 的全部补充规则'},
        'title': '格式测试2026', 'author': '测试人',
        'blocks': [
            {'type': 'paragraph', 'text': '正文测试ABC123。'},
            {'type': 'heading', 'level': 1, 'text': '一级标题'},
            {'type': 'heading', 'level': 2, 'text': '二级标题'},
            {'type': 'heading', 'level': 3, 'text': '三级标题'},
            {'type': 'heading', 'level': 4, 'text': '四级标题'},
            {'type': 'paragraph', 'text': '末段正文。'}],
        'signature': {'organization': '测试单位', 'date': '2026-10-28'},
        'attachments': [{'title': '测试附件', 'blocks': [{'type': 'paragraph', 'text': '附件正文。'}]}]
    }


class Rules(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.data = fixture()

    def tearDown(self):
        self.temp.cleanup()

    def parts(self):
        q.validate_input(self.data, self.base)
        return q.Builder(self.data, self.base).build()

    def doc(self):
        return E.fromstring(self.parts()['word/document.xml'])

    def test_valid_fixture(self):
        self.assertEqual(q.validate_input(self.data, self.base), self.data)

    def test_bad_inputs(self):
        cases = []
        d = fixture(); d['font'] = '宋体'; cases.append(d)
        d = fixture(); d['approval']['confirmation'] = '未确认'; cases.append(d)
        d = fixture(); d['blocks'][1]['level'] = 2; cases.append(d)
        d = fixture(); d['blocks'][1]['level'] = 5; cases.append(d)
        d = fixture(); d['blocks'][1]['text'] = '一、重复编号'; cases.append(d)
        d = fixture(); d['blocks'][0]['text'] = '文字\n换行'; cases.append(d)
        d = fixture(); d['blocks'][0]['text'] = '文字\t制表'; cases.append(d)
        d = fixture(); d['blocks'][0]['text'] = '**擅自加粗**'; cases.append(d)
        d = fixture(); d['blocks'][0]['text'] = '双  空格'; cases.append(d)
        d = fixture(); d['blocks'][0]['text'] = '\u3000首空格'; cases.append(d)
        d = fixture(); d['blocks'][0]['text'] = '全角２０２６'; cases.append(d)
        d = fixture(); d['blocks'][0]['color'] = 'red'; cases.append(d)
        d = fixture(); d['blocks'][0] = {'type': 'toc'}; cases.append(d)
        d = fixture(); d['attachments'] = []; cases.append(d)
        d = fixture(); d['signature']['date'] = '2026-02-30'; cases.append(d)
        for d in cases:
            with self.subTest(data=d):
                with self.assertRaises((q.Invalid, ValueError)):
                    q.validate_input(d, self.base)

    def test_duplicate_json_rejected(self):
        with self.assertRaises(q.Invalid):
            json.loads('{"title":"甲","title":"乙"}', object_pairs_hook=q.no_duplicates)

    def test_title_style(self):
        p = self.doc().find('w:body/w:p', q.NS)
        self.assertEqual(p.find('w:pPr/w:spacing', q.NS).get(q.tag('w:line')), '640')
        self.assertEqual(p.find('w:r/w:rPr/w:sz', q.NS).get(q.tag('w:val')), '44')
        self.assertEqual(p.find('w:pPr/w:jc', q.NS).get(q.tag('w:val')), 'center')

    def test_body_and_heading_indent(self):
        paragraphs = self.doc().findall('w:body/w:p', q.NS)
        for p in paragraphs[2:7]:
            self.assertEqual(p.find('w:pPr/w:ind', q.NS).get(q.tag('w:firstLineChars')), '200')
            self.assertEqual(p.find('w:pPr/w:spacing', q.NS).get(q.tag('w:lineRule')), 'exact')
            self.assertEqual(p.find('w:pPr/w:spacing', q.NS).get(q.tag('w:line')), '560')

    def test_numbering(self):
        texts = [''.join(p.itertext()) for p in self.doc().findall('w:body/w:p', q.NS)]
        for s in ['一、一级标题', '（一）二级标题', '1.三级标题', '（1）四级标题']:
            self.assertIn(s, texts)
        self.assertEqual(q.chinese_number(10), '十')
        self.assertEqual(q.chinese_number(21), '二十一')
        with self.assertRaises(q.Invalid): q.chinese_number(100)

    def test_latin_runs(self):
        for run in self.doc().findall('.//w:r', q.NS):
            t = run.find('w:t', q.NS)
            if t is not None and t.text and any(c.isascii() and c.isalnum() for c in t.text):
                f = run.find('w:rPr/w:rFonts', q.NS)
                self.assertEqual(f.get(q.tag('w:eastAsia')), 'Times New Roman')
                self.assertEqual(f.get(q.tag('w:hint')), 'default')

    def test_signature_exactly_two_real_blank_paragraphs(self):
        ps = self.doc().findall('w:body/w:p', q.NS)
        texts = [''.join(p.itertext()) for p in ps]
        i = texts.index('测试单位')
        self.assertEqual(texts[i-3:i], ['末段正文。', '', ''])
        self.assertEqual(texts[i+1], '2026年10月28日')

    def test_attachment_break(self):
        ps = self.doc().findall('w:body/w:p', q.NS)
        p = next(p for p in ps if ''.join(p.itertext()).startswith('附件1：'))
        self.assertEqual(p.find('w:pPr/w:pageBreakBefore', q.NS).get(q.tag('w:val')), '1')

    def test_duplex_footer(self):
        parts = self.parts()
        self.assertIn(b'evenAndOddHeaders', parts['word/settings.xml'])
        for n, alignment, indent in [(1, 'right', 'right'), (2, 'left', 'left')]:
            f = E.fromstring(parts[f'word/footer{n}.xml'])
            self.assertEqual(f.find('w:p/w:pPr/w:jc', q.NS).get(q.tag('w:val')), alignment)
            self.assertEqual(f.find('w:p/w:pPr/w:ind', q.NS).get(q.tag('w:'+indent)), '280')
            self.assertEqual(f.find('w:p/w:fldSimple', q.NS).get(q.tag('w:instr')), ' PAGE ')

    def table(self):
        return {'type': 'table', 'caption': '测试表格', 'headers': ['名称', '份数'], 'rows': [['测试', '1']], 'row_header': True}

    def test_table_rules(self):
        self.data['blocks'].insert(-1, self.table())
        doc = self.doc()
        table = doc.find('w:body/w:tbl', q.NS)
        self.assertIn('表1 测试表格', ''.join(doc.itertext()))
        self.assertEqual(len(table.findall('w:tblPr/w:tblBorders/*', q.NS)), 6)
        for b in table.findall('w:tblPr/w:tblBorders/*', q.NS):
            self.assertEqual(b.get(q.tag('w:sz')), '2')
        self.assertIn('名\u3000称', ''.join(table.itertext()))
        first_row = table.findall('w:tr', q.NS)[0]
        for r in first_row.findall('.//w:r', q.NS):
            self.assertEqual(r.find('w:rPr/w:b', q.NS).get(q.tag('w:val')), '1')
        rows = table.findall('w:tr', q.NS)
        for run in rows[0].findall('.//w:r', q.NS):
            self.assertEqual(run.find('w:rPr/w:b', q.NS).get(q.tag('w:val')), '1',
                             '表头行必须加粗')
        for row in rows[1:]:
            for run in row.findall('.//w:r', q.NS):
                self.assertEqual(run.find('w:rPr/w:b', q.NS).get(q.tag('w:val')), '0',
                                 '表头行以下全部行（含标题列）必须常规不加粗')

    def test_irregular_table_rejected(self):
        table = self.table(); table['rows'][0].append('多余单元格')
        self.data['blocks'].insert(-1, table)
        with self.assertRaises(q.Invalid): self.parts()

    def test_two_char_padding_only_labels(self):
        table = self.table()
        table.update({'row_header': False, 'rows': [['北京', '1']]})
        self.data['blocks'].insert(-1, table)
        doc = self.doc()
        texts = ''.join(doc.itertext())
        self.assertIn('北京', texts)
        self.assertNotIn('北\u3000京', texts)
        self.assertIn('名\u3000称', texts)

    def image(self, name='test.png', size=(200, 100)):
        from PIL import Image
        Image.new('RGB', size, 'white').save(self.base/name)
        return {'path': name, 'caption': '测试图片'}

    def test_body_image_anchor_not_inline(self):
        image = self.image()
        self.data['blocks'].insert(-1, {'type': 'figure', 'image': image})
        doc = self.doc()
        self.assertEqual(len(doc.findall('.//wp:anchor/wp:wrapTopAndBottom', q.NS)), 1)
        self.assertEqual(len(doc.findall('.//wp:inline', q.NS)), 0)
        self.assertIn('图1 测试图片', ''.join(doc.itertext()))

    def test_body_image_position_rejected(self):
        self.data['blocks'].append({'type': 'figure', 'image': self.image()})
        with self.assertRaises(q.Invalid): self.parts()

    def test_table_images_equal_sizes_inline_center(self):
        image = self.image()
        table = self.table(); table['row_header'] = False
        table['rows'] = [[{'image': image}, {'image': image}], [{'image': image}, {'image': image}]]
        self.data['blocks'].insert(-1, table)
        doc = self.doc()
        extents = doc.findall('.//wp:inline/wp:extent', q.NS)
        self.assertEqual(len(extents), 4)
        self.assertEqual(len({(p.get('cx'), p.get('cy')) for p in extents}), 1)
        for cell in doc.findall('.//w:tc', q.NS):
            self.assertEqual(cell.find('w:tcPr/w:vAlign', q.NS).get(q.tag('w:val')), 'center')
        texts = ''.join(doc.itertext())
        for i in range(1, 5): self.assertIn(f'图{i} 测试图片', texts)

    def test_image_aspect_mismatch_rejected(self):
        first, second = self.image(), self.image('other.png', (100, 100))
        table = self.table(); table['row_header'] = False
        table['rows'] = [[{'image': first}, {'image': second}]]
        self.data['blocks'].insert(-1, table)
        with self.assertRaises(q.Invalid): self.parts()

    def test_image_path_escape_rejected(self):
        with self.assertRaises(q.Invalid): q.relative_asset(self.base, '../a.png')

    def test_deterministic_and_valid_zip(self):
        parts = self.parts()
        self.assertEqual(parts, self.parts())
        output = self.base/'test.docx'
        q.write_package(parts, output)
        self.assertEqual(q.check_package(output, parts)['structure'], 'PASS')
        with self.assertRaises(q.Invalid): q.write_package(parts, output)

    def test_unauthorized_part_rejected(self):
        parts = self.parts(); wrong = dict(parts)
        wrong['word/vbaProject.bin'] = b'not-authorized'
        output = self.base/'tampered.docx'; q.write_package(wrong, output)
        with self.assertRaises(q.Invalid): q.check_package(output, parts)

    def test_style_mutations_rejected(self):
        parts = self.parts()
        for i, (old, new) in enumerate([(b'"640"', b'"600"'), (b'"000000"', b'"FF0000"'), (b'"44"', b'"48"'), (b'"200"', b'"100"')]):
            wrong = dict(parts)
            wrong['word/document.xml'] = wrong['word/document.xml'].replace(old, new, 1)
            output = self.base/f'bad{i}.docx'; q.write_package(wrong, output)
            with self.assertRaises(q.Invalid): q.check_package(output, parts)

    def test_duplicate_zip_entries_rejected(self):
        parts = self.parts(); output = self.base/'duplicate.docx'
        q.write_package(parts, output)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(output, 'a') as z:
                z.writestr('word/document.xml', parts['word/document.xml'])
        with self.assertRaises(q.Invalid): q.check_package(output, parts)

    def test_missing_fonts_blocked(self):
        path = self.base/'fonts.json'
        path.write_text(json.dumps({k: str(self.base/(k+'.ttf')) for k in q.FONTS}))
        with self.assertRaises(q.Invalid): q.font_check(path, self.data)

    def test_example_is_intentionally_unapproved(self):
        with self.assertRaises(q.Invalid):
            q.validate_input(q.load_json(ROOT/'examples/content.json'), ROOT/'examples')


if __name__ == '__main__':
    unittest.main(verbosity=2)
