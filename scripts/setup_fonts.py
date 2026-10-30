#!/usr/bin/env python3
"""按当前安装位置生成 work/fonts.json，并校验随包字体哈希。"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'assets' / 'fonts'
ROLES = ['title', 'body', 'kai', 'hei', 'latin']


def main():
    manifest = json.loads((FOLDER / 'manifest.json').read_text(encoding='utf-8'))
    if sorted(manifest) != sorted(ROLES):
        raise SystemExit(f'清单角色不完整：{sorted(manifest)}')

    config = {}
    for role in ROLES:
        item = manifest[role]
        path = FOLDER / item['file']
        if not path.is_file():
            raise SystemExit(f'缺少字体资源：{path}')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item['sha256']:
            raise SystemExit(f'字体资源校验失败：{role}；停止，禁止替换或绕过')
        config[role] = str(path)

    work = ROOT / 'work'
    work.mkdir(exist_ok=True)
    output = work / 'fonts.json'
    if output.exists():
        current = json.loads(output.read_text(encoding='utf-8'))
        if current != config:
            raise SystemExit(f'{output} 已存在且路径不同；请先人工确认后删除')
        print(output)
        return 0
    output.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n',
                      encoding='utf-8')
    print(output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
