import tempfile
from pathlib import Path

from format_sample import format_c_file, format_c_text


def test_format_c_text_is_generic_and_name_independent():
    src = '''
void sample(void)
{
    if ((a == 0) && (b == 1))
    {
        uint8_t x[10];
    }
}

void otherName(void)
{
    return;
}
'''

    out = format_c_text(src)

    assert 'void sample( void )' in out
    assert 'uint8_t x[ 10 ]' in out
    assert 'if ( ( a == 0 )\n      && ( b == 1 ) )' in out


def test_formats_array_access_function_arguments_and_logical_and():
    src = '''
uint8_t getValue(uint8_t id, uint8_t offset)
{
    if ((id == 0) && (offset == 1))
    {
        return values[id];
    }
}
'''

    out = format_c_text(src)

    assert 'uint8_t getValue( uint8_t id, uint8_t offset )' in out
    assert 'return values[ id ];' in out
    assert 'if ( ( id == 0 )\n      && ( offset == 1 ) )' in out


def test_logical_and_alignment_is_relative_to_the_if_indentation():
    src = '''
    if ((enabled == 1) && (ready == 1))
    {
        return;
    }
'''

    out = format_c_text(src)

    assert '    if ( ( enabled == 1 )\n      && ( ready == 1 ) )' in out
    assert format_c_text(out) == out


def test_recalculates_over_indented_if_and_logical_and_lines():
    src = '''
void run(void)
{
    if (((uint8_t)enabled == 1) && (ready == 1))
        {
            return;
        }
}
'''

    out = format_c_text(src)

    assert '    if ( ( (uint8_t)enabled == 1 )\n      && ( ready == 1 ) )' in out


def test_aligns_condition_group_closing_parentheses_to_the_longest_line():
    src = '''
if ((short == 0) && (longer_name == 1))
{
    return;
}
'''

    out = format_c_text(src)

    assert 'if ( ( short == 0       )\n  && ( longer_name == 1 ) )' in out


def test_inserts_spaces_around_comparison_operators_in_conditions():
    src = '''
if (value==0x00)
{
    return;
}
'''

    out = format_c_text(src)

    assert 'if ( value == 0x00 )' in out


def test_inserts_spaces_inside_parentheses_for_function_calls_with_arguments():
    src = '''
void run(void)
{
    result = add_u8(first, second);
}
'''

    out = format_c_text(src)

    assert 'result = add_u8( first, second );' in out


def test_joins_split_assignments_and_normalizes_assignment_spacing():
    src = '''
void run(void)
{
    result
    = add_u8(first, second);
}
'''

    out = format_c_text(src)

    assert 'result = add_u8( first, second );' in out


def test_joins_split_variable_declarations_and_empty_function_calls():
    src = '''
void run(void)
{
    uint8_t
    result;

    process
    ();
}
'''

    out = format_c_text(src)

    assert 'uint8_t result;' in out
    assert 'process();' in out


def test_joins_assignment_value_split_after_the_equals_sign():
    src = '''
void run(void)
{
    value =
    (uint8_t)0;
}
'''

    out = format_c_text(src)

    assert 'value = (uint8_t)0;' in out


def test_joins_three_line_assignments_and_normalizes_for_conditions():
    src = '''
void run(void)
{
    result
    =
    values[index];

    for (
    uint8_t index = 0;    index < (uint8_t)10;     index++)
    {
        if (value == (uint8_t)  0x00)
        {
            return;
        }
    }
}
'''

    out = format_c_text(src)

    assert 'result = values[ index ];' in out
    assert 'for ( uint8_t index = 0; index < (uint8_t)10; index++ )' in out
    assert 'if ( value == (uint8_t)0x00 )' in out


def test_adds_space_before_the_condition_group_close_on_and_lines():
    src = '''
if ( ( left == 0 )
  && ( right == 1))
{
    return;
}
'''

    out = format_c_text(src)

    assert '&& ( right == 1 ) )' in out


def test_normalizes_and_spacing_before_aligning_condition_closes():
    src = '''
if ( ( u8_test == (uint8_t)0x00 )
  && ( u8_another == (uint8_t)0x01))
{
    return;
}
'''

    out = format_c_text(src)

    assert 'if ( ( u8_test == (uint8_t)0x00    )' in out
    assert '&& ( u8_another == (uint8_t)0x01 ) )' in out


def test_writes_shift_jis_with_crlf_line_endings():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'sample.c'
        path.write_text('/* 日本語 */\nvoid run(void)\n{\n}\n', encoding='shift_jis', newline='\r\n')

        format_c_file(str(path))

        raw = path.read_bytes()
        assert '日本語'.encode('shift_jis') in raw
        assert b'\r\n' in raw
        assert b'\n' not in raw.replace(b'\r\n', b'')


def test_converts_existing_utf8_source_to_shift_jis():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'sample.h'
        path.write_text('/* 日本語 */\nvoid run(void);\n', encoding='utf-8', newline='\n')

        format_c_file(str(path))

        raw = path.read_bytes()
        assert '日本語'.encode('shift_jis') in raw
        assert '日本語'.encode('utf-8') not in raw
        assert b'\r\n' in raw


def test_inserts_one_space_after_argument_separator_commas():
    src = '''
uint8_t add(uint8_t left,uint8_t right);

void run(void)
{
    result = add(first,second);
}
'''

    out = format_c_text(src)

    assert 'uint8_t add( uint8_t left, uint8_t right );' in out
    assert 'result = add( first, second );' in out


def test_removes_spaces_between_a_cast_and_its_operand():
    src = '''
void run(void)
{
    (void)  value;
    result = (uint8_t)  0;
}
'''

    out = format_c_text(src)

    assert '(void)value;' in out
    assert 'result = (uint8_t)0;' in out
