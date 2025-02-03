import argparse

specialKeys = ['names', 'autoColumn', 'autoIncrement']

def add_argument(parser: argparse._ArgumentGroup, arg: dict):
    if 'type' in arg and arg['type'] == bool:
        arg = arg.copy()
        arg['action'] = 'store_true' if arg['default'] else 'store_false'
        del arg['type']
        del arg['default']
    parser.add_argument(*arg["names"], **{k: v for k, v in arg.items() if k not in specialKeys})

def create_parser(config):
    parser = argparse.ArgumentParser(
        prog=config.name,
        description=config.description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    for configType in ['inputs', 'advanced', 'outputs']:
        if hasattr(config, configType):
            arg_group = parser.add_argument_group(configType)
            for arg in getattr(config, configType):
                add_argument(arg_group, arg)
    
    return parser