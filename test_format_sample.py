from format_sample import format_c_text


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
