#! /usr/bin/env python3

'''
The Flex Transpiler.

Usage:
  flex_transpiler <source> -l <lang> [-o <output>]
  flex_transpiler -h

Arguments:
  <source>      Path to the input Flex source file.

Options:
  -l <lang>, --target-language <lang>   The target language to transpile to.
  -o <output>, --output <output>        Path to the generated output file.
  -h, --help                            Print this help text.

Target languages available:
  c++
  java
  python
'''

from os import listdir
import re

from docopt import docopt
from rasa_nlu.model import Interpreter

MAIN_REGEX = re.compile(r'Main\(\)\s*')
MODEL_DIR = './data/model/default/'


def generate_code(interpreted_data, code_dict):
    print()
    print(interpreted_data)
    print()
    intent = interpreted_data['intent']['name']

    kwargs = {}
    for entity in code_dict[intent]['entities']:
        for e in interpreted_data['entities']:
            if e['entity'] == entity:
                kwargs[entity] = e['value']

    return code_dict[intent]['code'].format_map(kwargs) + '\n'


def counts_tabs(line):
    num_tabs = 0
    for character in line:
        if character == '\t':
            num_tabs += 1
        else:
            break
    return num_tabs


if __name__ == '__main__':
    args = docopt(__doc__)
    source_file_path = args['<source>']
    target_language = args['--target-language']
    output_file_path = args['--output']

    # import code dictionary for target language
    if target_language == 'python':
        from languages.python import code_dict
    elif target_language == 'c++':
        from languages.c_plus_plus import code_dict
    elif target_language == 'java':
        from languages.java import code_dict

    # load NLU model
    interpreter = Interpreter.load(MODEL_DIR + listdir(MODEL_DIR)[0])

    # parse each line from the input file and store its transpiled code in the
    # `code` list
    code = [code_dict['default_code']]
    current_indent_level = 0
    prev_indent_level = 0
    with open(source_file_path, 'r') as source:
        source_lines = source.readlines()
        for line in source_lines:
            print(line, end='')
            current_indent_level = counts_tabs(line)
            if current_indent_level < prev_indent_level:
                code.append('\t' * current_indent_level + code_dict['end_block'])
            if not line.isspace():  # line is not "blank"
                if MAIN_REGEX.match(line):
                    code.append(code_dict['begin_main'])
                else:
                    interpreted_data = interpreter.parse(line.strip())
                    code.append('\t' * current_indent_level
                                + generate_code(interpreted_data, code_dict))
            prev_indent_level = current_indent_level
    while current_indent_level > 0:
        code.append('\t' * (current_indent_level - 1) + code_dict['end_block'])
        current_indent_level -= 1

    # write lines in `code` list to output file
    with open(output_file_path, 'w') as output:
        output.writelines(code)
        # special case: closing brace for the Java class
        if target_language == 'java':
            output.write('}')
