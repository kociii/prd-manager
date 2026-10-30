#!/usr/bin/env python3
"""Read-only layout checks for Markdown fenced ASCII wireframes (not component trees)."""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

def display_width(text):
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)

def forbidden(text):
    for char in text:
        code = ord(char)
        if char == '\t' or char == '\u3000' or unicodedata.category(char) in ('Cc', 'Cf'):
            return f'control/format/full-width space U+{code:04X}'
        if 0x1F000 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF or 0xFE00 <= code <= 0xFE0F or code == 0x20E3:
            return f'emoji or variable-width symbol U+{code:04X}'
    return None

def check_text(text, max_width=120):
    errors, warnings, blocks = [], [], []
    opened = None
    for number, line in enumerate(text.splitlines(), 1):
        fence = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
        if opened is None:
            if fence:
                opened = {'marker':fence[1][0], 'length':len(fence[1]), 'ascii':fence[2].strip() == 'ascii', 'start':number, 'lines':[]}
        elif fence and fence[1][0] == opened['marker'] and len(fence[1]) >= opened['length'] and not fence[2].strip():
            if opened['ascii']:
                blocks.append(opened)
            opened = None
        elif opened['ascii']:
            opened['lines'].append((number, line))
    if opened and opened['ascii']:
        errors.append(f'line {opened["start"]}: unclosed ascii fence')
    if not blocks:
        errors.append('No complete ascii wireframes found; nothing was validated')
    for block in blocks:
        rows = block['lines']
        if len(rows) < 3:
            errors.append(f'line {block["start"]}: wireframe needs top border, content and bottom border')
            continue
        expected = display_width(rows[0][1])
        for number, row in rows:
            bad = forbidden(row)
            if bad:
                errors.append(f'line {number}: {bad}; use plain spaces and text labels')
            actual = display_width(row)
            if actual != expected:
                errors.append(f'line {number}: display width {actual}, expected {expected}')
            border = re.fullmatch(r'\+(?:-+\+)+', row)
            content = row.startswith('|') and row.endswith('|')
            if not border and not content:
                errors.append(f'line {number}: row must be a +---+ border or |...| content row')
        for number, row in (rows[0], rows[-1]):
            if not re.fullmatch(r'\+(?:-+\+)+', row):
                errors.append(f'line {number}: first/last row must be a +---+ border')
        if rows[0][1] != rows[-1][1]:
            errors.append(f'line {block["start"]}: top and bottom borders differ')
        if expected > max_width:
            warnings.append(f'line {block["start"]}: {expected} columns exceeds suggested {max_width}; consider splitting')
    return errors, warnings, len(blocks)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('markdown', type=Path)
    parser.add_argument('--max-width', type=int, default=120, help='advisory display-column width')
    args = parser.parse_args()
    if args.max_width < 4:
        parser.error('--max-width must be at least 4')
    try:
        errors, warnings, count = check_text(args.markdown.read_text(encoding='utf-8'), args.max_width)
    except (OSError, UnicodeError) as error:
        print('ERROR:', error)
        return 1
    for message in errors:
        print('ERROR:', message)
    for message in warnings:
        print('WARNING:', message)
    if errors:
        return 1
    print(f'Layout checks passed: {count} ASCII wireframe(s). Review internal separators, hierarchy, interactions and design decisions separately.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
