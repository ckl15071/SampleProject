import argparse
import re
from pathlib import Path


def format_c_text(text: str) -> str:
    """Generic C text formatter.

    It rewrites only style patterns, never specific function or variable names,
    so adding new functions or arrays later will not require changing the formatter.
    """

    def normalize_function_signature(match):
        indent = match.group('indent')
        ret = match.group('ret').strip()
        name = match.group('name')
        args = match.group('args').strip()
        return f'{indent}{ret} {name}( {args} )'

    def normalize_array_subscript(match):
        name = match.group('name')
        index = match.group('index').strip()
        return f'{name}[ {index} ]'

    def normalize_condition(match):
        kw = match.group('kw')
        cond = match.group('cond').strip()
        cond = re.sub(r'\(\s*', '( ', cond)
        cond = re.sub(r'\s*\)', ' )', cond)
        return f'{kw} ( {cond} )'

    text = re.sub(
        r'(?m)^(?P<indent>[ \t]*)(?P<ret>[A-Za-z_][\w\s\*]*?)\s+(?P<name>[A-Za-z_][\w]*)\s*\(\s*(?P<args>[^()\n]*)\s*\)',
        normalize_function_signature,
        text,
    )

    text = re.sub(
        r'(?P<name>[A-Za-z_][\w]*)\s*\[\s*(?P<index>[^\[\]\n]+?)\s*\]',
        normalize_array_subscript,
        text,
    )

    text = re.sub(
        r'(?P<kw>if|for|while|switch)\s*\((?P<cond>[^\n{]+)\)',
        normalize_condition,
        text,
    )

    text = re.sub(
        r'\s+([=!<>]=?|&&|\|\||\+|-|\*|/|%)\s+',
        lambda m: f' {m.group(1)} ',
        text,
    )

    text = re.sub(
        r'(?m)^(?P<indent>[ \t]*)(?P<prefix>[^\n]*?)\s*&&\s*(?P<suffix>[^\n]+)$',
        lambda m: f'{m.group("indent")}{m.group("prefix").rstrip()}\n'
                  f'{m.group("indent")}  && {m.group("suffix").lstrip()}',
        text,
    )

    return text


def format_c_file(path: str = 'src/test/test.c') -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    file.write_text(format_c_text(text), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generic regex-based C formatter.')
    parser.add_argument('path', nargs='?', default='src/test/test.c')
    args = parser.parse_args()
    format_c_file(args.path)
