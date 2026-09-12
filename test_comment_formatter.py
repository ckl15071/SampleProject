import tempfile
from pathlib import Path

from comment_formatter import format_comments_file, format_comments_text, move_comments_to_next_multiple_of_four


def test_moves_line_comment_to_the_next_multiple_of_four_column():
    src = '    test(); // test\n'

    out = move_comments_to_next_multiple_of_four(src)

    assert out == '    test();     // test\n'


def test_moves_block_comment_to_the_next_multiple_of_four_column():
    src = '    value = 0; /* initialized */\n'

    out = move_comments_to_next_multiple_of_four(src)

    assert out == '    value = 0;  /* initialized */\n'


def test_keeps_column_one_comments_in_place():
    src = '// file header\n'

    out = move_comments_to_next_multiple_of_four(src)

    assert out == src


def test_keeps_comments_already_at_a_multiple_of_four_column():
    src = '    test();     // test\n'

    out = move_comments_to_next_multiple_of_four(src)

    assert out == src


def test_configuration_can_disable_comment_column_movement():
    src = '    test(); // test\n'

    out = format_comments_text(src, move_to_next_multiple_of_four=False)

    assert out == src


def test_preserves_input_encoding_and_line_endings_when_writing_a_file():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'sample.c'
        source = '    test(); // テスト\n'
        path.write_bytes(source.encode('utf-8'))

        format_comments_file(str(path))

        raw = path.read_bytes()
        assert 'テスト'.encode('utf-8') in raw
        assert 'テスト'.encode('shift_jis') not in raw
        assert b'\r\n' not in raw
        assert b'\n' in raw
