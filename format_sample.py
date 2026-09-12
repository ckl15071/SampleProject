import argparse
import json
import re
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name('format_config.json')


def load_config() -> dict:
    """フォーマッタ設定をJSONファイルから読み込む。"""
    with CONFIG_PATH.open(encoding='utf-8') as file:
        return json.load(file)


CONFIG = load_config()
SOURCE_ENCODING = CONFIG['source_encoding']
LINE_ENDING = CONFIG['line_ending']
# Trueの場合、変数宣言の型名と変数名の間を1スペースに統一する。
NORMALIZE_VARIABLE_DECLARATION_SPACING = CONFIG['normalize_variable_declaration_spacing']
# Trueの場合、引数なし関数呼び出しの括弧内空白を削除する。
NORMALIZE_EMPTY_FUNCTION_CALL_SPACING = CONFIG['normalize_empty_function_call_spacing']
# (uint8_t)value のようなキャストを判定するためのC型パターン。
CAST_TYPE_PATTERN = (
    r'(?:(?:const|volatile)\s+)*(?:(?:unsigned|signed|short|long)\s+)*'
    r'(?:void|char|int|float|double|bool|size_t|[A-Za-z_]\w*_t)(?:\s*\*+)?'
)


def read_source_text(path: Path) -> str:
    """Shift-JISを優先して読み込み、既存UTF-8ファイルも変換対象として受け付ける。"""
    try:
        # プロジェクトの出力文字コードを優先して読み込む。
        return path.read_text(encoding=SOURCE_ENCODING)
    except UnicodeDecodeError:
        # 初回のフォーマット時に既存UTF-8ファイルをShift-JISへ変換できるようにする。
        return path.read_text(encoding='utf-8')


def find_line_comment_start(line: str) -> int | None:
    """文字列・文字リテラルの外側にある末尾コメントの開始位置を返す。"""
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


def protect_trailing_comments(text: str) -> tuple[str, dict[str, tuple[int, str]]]:
    """末尾コメントを保護し、整形前の開始列を記録する。"""
    comments = {}
    lines = []

    for raw_line in text.splitlines(keepends=True):
        ending = '\r\n' if raw_line.endswith('\r\n') else '\n' if raw_line.endswith('\n') else ''
        line = raw_line[:-len(ending)] if ending else raw_line
        comment_start = find_line_comment_start(line)

        if comment_start is None or not line[:comment_start].strip():
            lines.append(raw_line)
            continue

        marker = f'__FORMATTER_COMMENT_{len(comments)}__'
        comments[marker] = (comment_start, line[comment_start:])
        lines.append(f'{line[:comment_start].rstrip()} {marker}{ending}')

    return ''.join(lines), comments


def restore_trailing_comments(text: str, comments: dict[str, tuple[int, str]]) -> str:
    """保護した末尾コメントを、整形前の開始列へ戻す。"""
    for marker, (column, comment) in comments.items():
        marker_start = text.find(marker)
        if marker_start < 0:
            continue

        line_start = text.rfind('\n', 0, marker_start) + 1
        code = text[line_start:marker_start].rstrip(' \t')
        padding = ' ' * max(1, column - len(code))
        text = f'{text[:line_start]}{code}{padding}{comment}{text[marker_start + len(marker):]}'

    return text


def normalize_indentation(text: str) -> str:
    """波括弧のネスト深さからインデントを決め、&&継続行は2スペース深くする。"""
    depth = 0
    lines = []

    for raw_line in text.splitlines(keepends=True):
        # 最終書き込みで改行コードを統一するまで、行ごとの改行は保持する。
        ending = '\r\n' if raw_line.endswith('\r\n') else '\n' if raw_line.endswith('\n') else ''
        body = raw_line[:-len(ending)] if ending else raw_line
        content = body.lstrip(' \t')

        if not content:
            lines.append(ending)
            continue

        # 文字列リテラルと行コメント内の波括弧はブロック階層に数えない。
        code = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '', content)
        code = code.split('//', maxsplit=1)[0]
        starts_with_close_brace = code.lstrip().startswith('}')
        line_depth = max(depth - 1, 0) if starts_with_close_brace else depth

        if content.startswith('#'):
            # プリプロセッサディレクティブは行頭を維持する。
            lines.append(content + ending)
        else:
            # &&の継続行は制御文より2スペース深くする。
            continuation = 2 if code.lstrip().startswith('&&') else 0
            lines.append(f'{" " * (line_depth * 4 + continuation)}{content}{ending}')

        depth = max(depth + code.count('{') - code.count('}'), 0)

    return ''.join(lines)


def normalize_and_condition_group_close(text: str) -> str:
    """&&条件行の内側の閉じ括弧直前を1スペースにする。"""
    def normalize(match):
        condition = re.sub(r'\s*(==|!=|<=|>=|<|>)\s*', r' \1 ', match.group('condition'))
        return f'{match.group("indent")}&& ( {condition.rstrip()} ){match.group("outer")}'

    return re.sub(
        r'(?m)^(?P<indent>[ \t]*)&&[ \t]*\([ \t]*(?P<condition>.*\S)[ \t]*\)'
        r'(?P<outer>[ \t]*\)[ \t]*)$',
        normalize,
        text,
    )


def join_control_condition_line_breaks(text: str) -> str:
    """制御文または&&の開き括弧直後にある改行を結合する。"""
    text = re.sub(
        r'(?m)^(?P<indent>[ \t]*)(?P<keyword>if|for|while|switch|&&)[ \t]*\([ \t]*\r?\n'
        r'[ \t]*(?P<condition>[^\r\n]+)',
        lambda m: f'{m.group("indent")}{m.group("keyword")} ( {m.group("condition").lstrip()}',
        text,
    )
    return re.sub(
        r'(?m)^(?P<condition>[ \t]*(?:if|for|while|switch|&&)[^\r\n]*)\r?\n'
        r'[ \t]*(?P<close>\)+)[ \t]*$',
        lambda m: f'{m.group("condition").rstrip()}{m.group("close")}',
        text,
    )


def align_condition_closing_parentheses(text: str) -> str:
    """&&で連結された2行の条件グループの閉じ括弧を同じ列に揃える。"""
    pattern = re.compile(
        r'(?m)^(?P<left_prefix>[ \t]*(?:if|for|while|switch)\s+\(\s+\()'
        r'(?P<left_body>.*?\S)(?P<left_padding>[ \t]*)\)'
        r'(?P<left_suffix>[ \t]*)(?P<ending>\r?\n)'
        r'(?P<right_prefix>[ \t]*&&\s+\(\s+)'
        r'(?P<right_body>.*?\S)(?P<right_padding>[ \t]*)\)'
        r'(?P<right_suffix>[ \t]*\)[ \t]*)$'
    )

    def align(match):
        # 空白を正規化してから、より右側の閉じ括弧の位置を基準にする。
        left_content_column = len(match.group('left_prefix')) + len(match.group('left_body'))
        right_content_column = len(match.group('right_prefix')) + len(match.group('right_body'))
        target_column = max(left_content_column, right_content_column) + 1
        left_padding = ' ' * (target_column - left_content_column)
        right_padding = ' ' * (target_column - right_content_column)
        right_outer_close = match.group('right_suffix').strip()
        return (
            f'{match.group("left_prefix")}{match.group("left_body")}{left_padding})'
            f'{match.group("left_suffix")}{match.group("ending")}'
            f'{match.group("right_prefix")}{match.group("right_body")}{right_padding})'
            f' {right_outer_close}'
        )

    return pattern.sub(align, text)


def format_c_text(
    text: str,
    normalize_declaration_spacing: bool = NORMALIZE_VARIABLE_DECLARATION_SPACING,
    normalize_empty_function_call_spacing: bool = NORMALIZE_EMPTY_FUNCTION_CALL_SPACING,
) -> str:
    """汎用的なCソース文字列フォーマッタ。

    特定の関数名や変数名ではなく書式パターンだけを変換するため、
    後から関数や配列を追加してもフォーマッタ本体の変更は不要。
    """

    # 同一行のコード幅が変わっても、末尾コメントの開始列を維持する。
    text, trailing_comments = protect_trailing_comments(text)

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

    def normalize_function_call(match):
        name = match.group('name')
        args = match.group('args').strip()
        if name in {'if', 'for', 'while', 'switch'}:
            return match.group(0)
        return f'{name}( {args} )'

    def normalize_condition(match):
        kw = match.group('kw')
        cond = match.group('cond').strip()
        cond = re.sub(r'\(\s*', '( ', cond)
        cond = re.sub(r'\s*\)', ' )', cond)
        cond = re.sub(r'\s*(==|!=|<=|>=|<|>)\s*', r' \1 ', cond)
        cond = re.sub(
            rf'\(\s*(?P<type>{CAST_TYPE_PATTERN})\s*\)',
            lambda m: f'({re.sub(r"\s+", " ", m.group("type")).strip()})',
            cond,
        )
        cond = re.sub(rf'(?P<cast>\({CAST_TYPE_PATTERN}\))[ \t]+', r'\g<cast>', cond)
        cond = re.sub(r'\s*;\s*', '; ', cond)
        return f'{kw} ( {cond} )'

    # 誤って同じ行になった連続#includeを、個別のプリプロセッサ行に戻す。
    text = re.sub(
        r'(?m)^(?P<first>[ \t]*#include[^\r\n]*?)[ \t]+(?P<next>#include\b)',
        lambda m: f'{m.group("first")}\n{m.group("next")}',
        text,
    )

    # 関数宣言・定義を name( arguments ) の形に整える。
    text = re.sub(
        r'(?m)^(?P<indent>[ \t]*)(?P<ret>[A-Za-z_][\w\s\*]*?)\s+(?P<name>[A-Za-z_][\w]*)\s*\(\s*(?P<args>[^()\n]*)\s*\)',
        normalize_function_signature,
        text,
    )

    # 配列の宣言・アクセスを array[ index ] の形に整える。
    text = re.sub(
        r'(?P<name>[A-Za-z_][\w]*)\s*\[\s*(?P<index>[^\[\]\n]+?)\s*\]',
        normalize_array_subscript,
        text,
    )

    # 手動改行で型と宣言子が分かれた変数宣言を結合する。
    declaration_type = (
        r'(?:(?:const|volatile|static|extern|unsigned|signed|short|long)\s+)*'
        r'(?:struct\s+[A-Za-z_][\w]*|enum\s+[A-Za-z_][\w]*|'
        r'union\s+[A-Za-z_][\w]*|[A-Za-z_][\w]*)(?:[ \t]*\*+)?'
    )
    text = re.sub(
        rf'(?m)^(?P<indent>[ \t]*)(?P<type>{declaration_type})[ \t]*(?:\r?\n[ \t]*)+'
        r'[ \t]*(?P<name>[A-Za-z_][\w]*(?:[ \t]*\[[^\]\n]*\])?)[ \t]*;',
        lambda m: f'{m.group("indent")}{m.group("type")} {m.group("name")};',
        text,
    )
    if normalize_declaration_spacing:
        # 同一行にある変数宣言の型名と変数名の間を1スペースにする。
        text = re.sub(
            rf'(?m)^(?P<indent>[ \t]*)(?!(?:return|break|continue|goto)\b)'
            rf'(?P<type>{declaration_type})[ \t]+(?P<name>[A-Za-z_][\w]*'
            r'(?:[ \t]*\[[^\]\n]*\])?)[ \t]*;',
            lambda m: f'{m.group("indent")}{m.group("type").strip()} {m.group("name")};',
            text,
        )
    text = re.sub(
        r'(?m)^(?P<indent>[ \t]*)(?P<name>[A-Za-z_][\w]*)[ \t]*\r?\n'
        r'[ \t]*\(\s*\)[ \t]*;',
        lambda m: f'{m.group("indent")}{m.group("name")}();',
        text,
    )

    # 代入記号周辺で分かれた手動改行・空行を結合し、=の前後を各1スペースにする。
    assignment_target = (
        r'[A-Za-z_][\w]*(?:[ \t]*(?:\.|->)[ \t]*[A-Za-z_][\w]*'
        r'|[ \t]*\[[^\]\n]+\])*'
    )
    text = re.sub(
        rf'(?m)^(?P<indent>[ \t]*)(?P<lhs>{assignment_target})[ \t]*\r?\n'
        r'[ \t]*=[ \t]*\r?\n(?:[ \t]*\r?\n)*[ \t]*(?P<rhs>[^\n;]+;)',
        lambda m: f'{m.group("indent")}{m.group("lhs")} = {m.group("rhs").strip()}',
        text,
    )
    text = re.sub(
        rf'(?m)^(?P<indent>[ \t]*)(?P<lhs>{assignment_target})[ \t]*\r?\n'
        rf'[ \t]*=[ \t]*(?P<cast>\(\s*{CAST_TYPE_PATTERN}\s*\))[ \t]*\r?\n'
        r'[ \t]*(?P<value>[^\n;]+;)',
        lambda m: f'{m.group("indent")}{m.group("lhs")} = '
                  f'{m.group("cast")}{m.group("value").strip()}',
        text,
    )
    # 引数ありの関数呼び出しを name( arguments ) の形に整える。
    text = re.sub(
        rf'(?m)^(?P<indent>[ \t]*)(?P<lhs>{assignment_target})[ \t]*=[ \t]*\r?\n'
        r'[ \t]*(?P<rhs>[^\n;]+;)',
        lambda m: f'{m.group("indent")}{m.group("lhs")} = {m.group("rhs").strip()}',
        text,
    )
    text = re.sub(
        rf'(?m)^(?P<indent>[ \t]*)(?P<lhs>{assignment_target})[ \t]*\r?\n'
        r'[ \t]*=[ \t]*(?P<rhs>[^\n;]+;)',
        lambda m: f'{m.group("indent")}{m.group("lhs")} = {m.group("rhs").strip()}',
        text,
    )
    text = re.sub(
        rf'(?m)^(?P<indent>[ \t]*)(?P<lhs>{assignment_target})[ \t]*='
        r'[ \t]*(?P<rhs>[^\n;]+;)',
        lambda m: f'{m.group("indent")}{m.group("lhs")} = {m.group("rhs").strip()}',
        text,
    )

    text = re.sub(
        r'(?P<name>[A-Za-z_][\w]*)\s*\(\s*(?P<args>[^()\n]+?)\s*\)',
        normalize_function_call,
        text,
    )
    if normalize_empty_function_call_spacing:
        # 引数なし関数呼び出しの括弧内にある空白を削除する。
        text = re.sub(r'(?P<name>[A-Za-z_][\w]*)\([ \t]*\)', r'\g<name>()', text)

    # 引数・初期化子の区切りコンマ後を1スペースにする。
    text = re.sub(r',[ \t]*', ', ', text)

    # 比較演算子直後の改行を結合して、条件式を1行として扱えるようにする。
    text = re.sub(
        r'(?m)^(?![ \t]*#)(?P<prefix>[ \t]*[^\r\n]*?(?:==|!=|<=|>=|<|>))[ \t]*\r?\n'
        r'[ \t]*(?P<rhs>[^\r\n]+)',
        lambda m: f'{m.group("prefix").rstrip()} {m.group("rhs").lstrip()}',
        text,
    )

    # 制御文・&&の開き括弧直後に残る改行を先に結合する。
    text = join_control_condition_line_breaks(text)

    # 分割済みif条件は、先頭行の条件書式を処理する前に整える。
    text = normalize_and_condition_group_close(text)

    # 開き括弧直後で分割されたforヘッダを1行に戻す。
    text = re.sub(
        r'(?m)^(?P<indent>[ \t]*)(?P<kw>for)[ \t]*\([ \t]*\r?\n'
        r'[ \t]*(?P<condition>[^\n{]+\))[ \t]*$',
        lambda m: f'{m.group("indent")}{m.group("kw")} ( {m.group("condition").strip()}',
        text,
    )

    # 条件行が揃った後で、条件式専用の空白規則を適用する。
    text = re.sub(
        r'(?P<kw>if|for|while|switch)\s*\((?P<cond>[^\n{]+)\)',
        normalize_condition,
        text,
    )

    # 改行を変えずに、二項演算子前後の空白を整える。
    text = re.sub(
        r'[ \t]+([=!<>]=?|&&|\|\||\+|-|\*|/|%)[ \t]+',
        lambda m: f' {m.group(1)} ',
        text,
    )

    # キャスト内部と、閉じ括弧と被キャスト値の間の空白を削除する。
    text = re.sub(
        rf'\([ \t]*(?P<type>{CAST_TYPE_PATTERN})[ \t]*\)(?=[ \t]*(?:[A-Za-z_]|[0-9]|\())',
        lambda m: f'({re.sub(r"\s+", " ", m.group("type")).strip()})',
        text,
    )
    text = re.sub(rf'(?P<cast>\({CAST_TYPE_PATTERN}\))[ \t]+', r'\g<cast>', text)

    # 文末セミコロンの直前にある空白を削除する。
    text = re.sub(r'[ \t]+;', ';', text)

    # 制御文ヘッダの直後にある波括弧を、次の行へ移動する。
    text = re.sub(
        r'(?m)^(?P<header>[ \t]*(?:if|for|while|switch)\b[^\r\n{]*\))[ \t]*\{[ \t]*$',
        lambda m: f'{m.group("header").rstrip()}\n{m.group("header")[:len(m.group("header")) - len(m.group("header").lstrip())]}{{',
        text,
    )

    # 1行内の&&条件を、位置揃え対象の継続行へ分割する。
    text = re.sub(
        r'(?m)^(?P<indent>[ \t]*)(?P<prefix>\S[^\n]*?)\s*&&\s*(?P<suffix>[^\n]+)$',
        lambda m: f'{m.group("indent")}{m.group("prefix").rstrip()}\n'
                  f'{m.group("indent")}  && {m.group("suffix").lstrip()}',
        text,
    )

    # 条件式内空白を確定してから列を揃え、最後にブロックのインデントを適用する。
    text = normalize_and_condition_group_close(text)
    text = align_condition_closing_parentheses(text)
    text = normalize_indentation(text)
    text = restore_trailing_comments(text, trailing_comments)
    # 行末の不要なスペースとタブを削除する。
    return re.sub(r'(?m)[ \t]+$', '', text)


def format_c_file(path: str = 'src/test/test.c') -> None:
    """1つのソースファイルを整形し、Shift-JIS・CRLFで書き込む。"""
    file = Path(path)
    text = read_source_text(file)
    file.write_text(format_c_text(text), encoding=SOURCE_ENCODING, newline=LINE_ENDING)


if __name__ == '__main__':
    # 対象ファイルを引数で受け取り、省略時は従来のサンプルを対象にする。
    parser = argparse.ArgumentParser(description='Generic regex-based C formatter.')
    parser.add_argument('path', nargs='?', default='src/test/test.c')
    args = parser.parse_args()
    format_c_file(args.path)
