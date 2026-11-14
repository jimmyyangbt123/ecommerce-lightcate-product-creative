#!/usr/bin/env python3
"""Offline repository integrity checks; not an image/model quality benchmark."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'ecommerce-product-creative'


def validate():
    errors = []
    required = [
        'README.md', 'NOTICE.md', 'CHANGELOG.md', 'CONTRIBUTING.md',
        'docs/WORKFLOW.md', 'docs/TESTING.md', 'docs/RELIABILITY.md', 'docs/RELEASE_CHECKLIST.md',
        'examples/STARTERS.md', 'examples/DELIVERY_EXAMPLE.md', 'examples/delivery.json',
        '.github/workflows/validate.yml', 'tests/test_quantity.py',
        'skills/ecommerce-product-creative/SKILL.md',
        'skills/ecommerce-product-creative/agents/openai.yaml',
        'skills/ecommerce-product-creative/scripts/check_delivery.py',
        'skills/ecommerce-product-creative/references/quantity.md',
    ]
    for name in required:
        if not (ROOT / name).is_file():
            errors.append(f'Missing file: {name}')
    for path in ROOT.rglob('*.md'):
        if '.git' in path.parts:
            continue
        content = path.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)', content):
            if '://' in target or target.startswith(('#', 'mailto:')):
                continue
            target_path = target.split('#', 1)[0]
            if target_path and not (path.parent / target_path).exists():
                errors.append(f'Broken local link: {path.relative_to(ROOT)} -> {target}')
        if content.count('```') % 2:
            errors.append(f'Unclosed fenced block: {path.relative_to(ROOT)}')
        for marker in ('/home/agent/', '/workspace/scratch/', 'git-authed/skills', 'libfile_'):
            if marker in content:
                errors.append(f'Private workspace marker in {path.relative_to(ROOT)}: {marker}')
    entry = SKILL / 'SKILL.md'
    if entry.exists():
        content = entry.read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not match or not re.search(r'^name: ecommerce-product-creative$', match[1], re.MULTILINE):
            errors.append('Invalid or unexpected skill frontmatter name')
        if not match or not re.search(r'^description: \S', match[1], re.MULTILINE):
            errors.append('Missing skill description')
        if len(content.splitlines()) >= 500:
            errors.append('Skill entry must remain below 500 lines')
    return errors


if __name__ == '__main__':
    problems = validate()
    for problem in problems:
        print(f'FAIL: {problem}', file=sys.stderr)
    if problems:
        raise SystemExit(1)
    print('PASS: expected files, local links, Markdown fences, privacy markers and skill entry structure.')
