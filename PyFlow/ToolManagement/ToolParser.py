import argparse
from pathlib import Path
from pydoc import locate

specialKeys = ['name', 'autoColumn', 'autoIncrement', 'shortname', 'advanced', 'decimals', 'static']

def add_argument(parser: argparse._ArgumentGroup, arg: dict):
    if 'type' in arg and arg['type'] == 'bool':
        arg = arg.copy()
        arg['action'] = 'store_false' if arg.get('default', False) else 'store_true'
        del arg['type']
        if 'default' in arg:
            del arg['default']
    kwargs = {k: v for k, v in arg.items() if k not in specialKeys}
    if 'type' in kwargs:
        kwargs['type'] = locate(kwargs['type']) if kwargs['type'] != 'Path' else Path
    parser.add_argument('--' + arg["name"], **kwargs)

def create_parser(config):
    parser = argparse.ArgumentParser(
        prog=config.name,
        description=config.description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    for configType in ['inputs', 'outputs']:
        if hasattr(config, configType):
            arg_group = parser.add_argument_group(configType)
            for arg in getattr(config, configType):
                add_argument(arg_group, arg)
    
    return parser