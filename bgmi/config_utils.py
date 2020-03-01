import configparser
from typing import Any, Dict

import chardet

from bgmi.models.config import Config, WritableConfig


def dump_v(v):
    if isinstance(v, str):
        return v
    elif isinstance(v, bool):
        return '1' if v else '0'
    elif v is None:
        return ''
    elif isinstance(v, list):
        return ', '.join(v)
    return str(v)


def load_config(parser: configparser.ConfigParser) -> dict:
    """convert ConfigParser to a nested dict"""
    default_section = 'bgmi'
    root: Dict[str, Any] = {}
    for section in parser.sections():
        if section == default_section:
            continue
        section_dict = {}
        for key, value in parser.items(section):
            section_dict[key] = value
        root[section] = section_dict

    for key, value in parser.items(default_section):
        root[key.upper()] = value

    return root


def dump_config(config: WritableConfig) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    default_section = 'bgmi'
    parser.add_section(default_section)
    parser.add_section('KEYWORD WEIGHT')
    inst = Config()
    data = inst.dict(by_alias=True)
    for key, value in data.items():

        if key == 'DOWNLOAD_DELEGATE':
            parser.add_section(value)

        if isinstance(value, dict):
            if key in ['KEYWORD WEIGHT', config.DOWNLOAD_DELEGATE]:
                for k, v in value.items():
                    parser.set(key, k, dump_v(v))

        else:
            parser.set(default_section, key, dump_v(value))
    return parser


def get_config_parser_and_read(config_file_path: str) -> configparser.ConfigParser:
    try:
        with open(config_file_path, encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(config_file_path, 'rb') as fb:
            byte_content = fb.read()
        encoding = chardet.detect(byte_content)
        content = byte_content.decode(encoding.get('encoding'))

    c = configparser.ConfigParser()
    c.read_string(content)
    return c


def write_config_parser(config_parser: configparser.ConfigParser, config_file_path):
    with open(config_file_path, 'w+', encoding='utf-8') as f:
        config_parser.write(f)
