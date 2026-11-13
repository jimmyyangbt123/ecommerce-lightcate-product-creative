#!/usr/bin/env python3
"""Check declared pack-count prefixes; does not inspect images or verify supplier data."""
import json
from pathlib import Path
import sys


def quantity_label(counts):
    if not isinstance(counts, list) or not counts:
        raise ValueError('pack_counts must be a non-empty list')
    if any(type(n) is not int or n <= 0 for n in counts):
        raise ValueError('pack_counts must contain positive integers, not booleans/strings')
    if len(set(counts)) != len(counts):
        raise ValueError('pack_counts must not contain duplicates')
    return '/'.join(str(n) for n in sorted(counts)) + 'pc'


def has_prefix(text, label):
    if not isinstance(text, str):
        return False
    text = text.strip()
    return text == label or (text.startswith(label) and len(text) > len(label) and text[len(label)].isspace())


def validate(document):
    errors = []
    if not isinstance(document, dict) or not isinstance(document.get('listings'), list) or not document['listings']:
        return ['listings must be a non-empty list']
    seen = set()
    for index, listing in enumerate(document['listings']):
        key = f'listings[{index}]'
        if not isinstance(listing, dict):
            errors.append(f'{key} must be an object')
            continue
        identity = listing.get('id')
        if not isinstance(identity, str) or not identity.strip():
            errors.append(f'{key}.id must be a non-empty string')
        elif identity in seen:
            errors.append(f'{key}.id duplicates {identity}')
        else:
            seen.add(identity)
        try:
            label = quantity_label(listing.get('pack_counts'))
        except ValueError as exc:
            errors.append(f'{key}: {exc}')
            continue
        for field in ('title', 'cover_header'):
            if not has_prefix(listing.get(field), label):
                errors.append(f'{key}.{field} must start with {label!r} followed by whitespace or end of text')
    return errors


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 scripts/check_delivery.py delivery.json', file=sys.stderr)
        return 2
    try:
        document = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        print(f'Input error: {exc}', file=sys.stderr)
        return 2
    errors = validate(document)
    if errors:
        for error in errors:
            print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print('PASS: declared title/cover text prefixes match declared pack options. Image and fact review still required.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
