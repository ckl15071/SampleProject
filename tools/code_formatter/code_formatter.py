import argparse

from format_sample import format_c_file, format_c_text

__all__ = ['format_c_file', 'format_c_text']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generic regex-based C formatter.')
    parser.add_argument('path', nargs='?', default='src/test/test.c')
    args = parser.parse_args()
    format_c_file(args.path)
