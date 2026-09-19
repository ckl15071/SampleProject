import argparse
import json
import re
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name('comment_format_config.json')
COMMENT_COLUMN_STEP = 4


def load_config() -> dict:
    """コメント整形用JSONから設定を読み込む。"""
    with CONFIG_PATH.open(encoding='utf-8') as file:
        return json.load(file)


CONFIG = load_config()
MOVE_COMMENTS_TO_NEXT_MULTIPLE_OF_FOUR = CONFIG['move_comments_to_next_multiple_of_four']


def read_source_file(path: Path) -> tuple[str, str]:
    """入力ファイルの文字コードを判定し、改行を変換せずに読み込む。"""
    raw = path.read_bytes()
    try:
        return raw.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        return raw.decode('shift_jis'), 'shift_jis'


def find_comment_start(line: str) -> int | None:
    """文字列・文字リテラル外の//または/*の開始位置を返す。"""
    quote = None
    escaped = False

    for index, character in enumerate(line[:-1]):
        if quote:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == '/' and line[index + 1] in {'/', '*'}:
            return index

    return None


def strip_literals_and_comments(line: str) -> str:
    """インデント計算用に文字列・文字リテラル・行末コメントを除外する。"""
    comment_start = find_comment_start(line)
    code = line[:comment_start] if comment_start is not None else line
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '', code)


def align_comment_only_indentation(text: str) -> str:
    """コメントだけの行を、その時点のコードブロックのインデントへ揃える。"""
    depth = 0
    in_block_comment = False
    lines = []

    for raw_line in text.splitlines(keepends=True):
        ending = '\r\n' if raw_line.endswith('\r\n') else '\n' if raw_line.endswith('\n') else ''
        line = raw_line[:-len(ending)] if ending else raw_line
        content = line.lstrip(' \t')
        comment_start = find_comment_start(line)
        comment_only = in_block_comment or (
            comment_start is not None and not line[:comment_start].strip()
        )

        if comment_only:
            lines.append(f'{" " * (depth * COMMENT_COLUMN_STEP)}{content}{ending}')
            if '/*' in content and '*/' not in content:
                in_block_comment = True
            elif '*/' in content:
                in_block_comment = False
            continue

        lines.append(raw_line)
        code = strip_literals_and_comments(line)
        depth = max(depth + code.count('{') - code.count('}'), 0)

    return ''.join(lines)


def move_comments_to_next_multiple_of_four(text: str) -> str:
    """1列目以外のコメント開始位置を、右方向の4の倍数列へ移動する。"""
    lines = []

    for raw_line in text.splitlines(keepends=True):
        ending = '\r\n' if raw_line.endswith('\r\n') else '\n' if raw_line.endswith('\n') else ''
        line = raw_line[:-len(ending)] if ending else raw_line
        comment_start = find_comment_start(line)

        if comment_start in {None, 0}:
            lines.append(raw_line)
            continue

        target_column = ((comment_start + COMMENT_COLUMN_STEP - 1) // COMMENT_COLUMN_STEP
                         * COMMENT_COLUMN_STEP)
        code = line[:comment_start].rstrip(' \t')
        comment = line[comment_start:].rstrip(' \t')
        lines.append(f'{code}{" " * (target_column - len(code))}{comment}{ending}')

    return ''.join(lines)


def format_comments_text(
    text: str,
    move_to_next_multiple_of_four: bool = MOVE_COMMENTS_TO_NEXT_MULTIPLE_OF_FOUR,
) -> str:
    """設定に従い、既存コメント開始位置を4の倍数列へ整える。"""
    if not move_to_next_multiple_of_four:
        return text
    return move_comments_to_next_multiple_of_four(text)


def format_comments_file(path: str) -> None:
    """コメント位置だけを整え、入力時の文字コード・改行コードを保持して書き込む。"""
    file = Path(path)
    text, encoding = read_source_file(file)
    file.write_bytes(format_comments_text(text).encode(encoding))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='C source comment alignment formatter.')
    parser.add_argument('path')
    args = parser.parse_args()
    format_comments_file(args.path)
