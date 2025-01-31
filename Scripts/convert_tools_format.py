from importlib import import_module
import sys
import re
from pathlib import Path

import argparse

# Function to convert the parser arguments to the desired dictionary format
def convert_parser_to_dict(parser, custom_settings):
    inputs = []
    advanced = []
    outputs = []
    
    for action in parser._actions:
        if action.dest == 'help': continue
        arg_dict = {
            'names': action.option_strings,
            'help': action.help,
        }
        if hasattr(action, 'required') and action.required:
            arg_dict['required'] = action.required
        elif hasattr(action, 'default') and action.default is not argparse.SUPPRESS:
            arg_dict['default'] = action.default

        if hasattr(action, 'choices') and action.choices:
            arg_dict['choices'] = list(action.choices)
        if hasattr(action, 'type') and action.type is not None:
            arg_dict['type'] = action.type.__name__
        if hasattr(action, 'action') and (action == 'store_true' or action == 'store_false'):
            arg_dict['type'] = bool
            arg_dict['default'] = action == 'store_true'
        
        # Check if there's a custom setting (like autoColumn)
        if action.dest in custom_settings:
            arg_dict.update(custom_settings[action.dest])
        
        if action.container.title == 'inputs':
            inputs.append(arg_dict)
        if action.container.title == 'advanced':
            advanced.append(arg_dict)
        elif action.container.title == 'outputs':
            outputs.append(arg_dict)
        
    return {
        'name': parser.prog,
        'description': parser.description,
        'inputs': inputs,
        'advanced': advanced,
        'outputs': outputs,
    }

def dict_to_formatted_string(d):
    def format_value(value, isType):
        if isinstance(value, str):
            return value if isType else f"'{value}'"
        elif isinstance(value, list):
            return "[" + ", ".join(format_value(v, False) for v in value) + "]"
        elif isinstance(value, dict):
            raise Exception('Unimplemented')
            # return dict_to_formatted_string(value)
        else:
            return value if isType else str(value)

    def format_dict(d):
        lines = ["    dict("]
        for k, v in d.items():
            lines.append(f"                {k} = {format_value(v, k=='type')},")
        lines.append("            )")
        return "\n".join(lines)

    lines = []
    for key in ['name', 'description']:
        lines.append(f'    {key} = "{d[key]}"')
    
    for section in ['inputs', 'outputs']:
        lines.append(f'    {section} = [')
        for item in d[section]:
            lines.append('        ' + format_dict(item) + ',')
        lines.append('    ]')

    return "\n".join(lines)


def convert_script(script_path, tool_description):
    with open(script_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Extract the content before the getArgumentParser function
    before_gap_match = re.search(r'(.*?)(?=def getArgumentParser\(.*?\):)', content, re.DOTALL)
    before_gap = before_gap_match.group(0) if before_gap_match else content

    # Extract the content after the getArgumentParser function
    after_gap_match = re.search(r'return parser, dict[^\n]*(.*)', content, re.DOTALL)
    after_gap = after_gap_match.group(1) if after_gap_match else content

    new_content = dict_to_formatted_string(tool_description)
    
    # Combine the unchanged part and new content
    result_content = before_gap.replace('\n    @staticmethod\n', '') + '\n' + new_content + after_gap
    
    result_content = result_content.split("if __name__ == '__main__':")[0]
    result_content.replace('import argparse\n', '')

    # Write the new content
    with open(script_path, "w", encoding="utf-8") as file:
        file.write(result_content)

base_dir = "/Users/amasson/Travail/bioimageit/PyFlow/Tools"

for tool_folder in sorted(list(Path(base_dir).iterdir())):
    if not tool_folder.is_dir(): continue
    for file in sorted(list(tool_folder.iterdir())):
        if file.suffix == ".py" and file.name != 'cellpose_segment.py':

            # Get the parser and custom settings from the getArgumentParser function

            sys.path.append(str(file.parent))
            # module = import_module(file.stem)
            import importlib
            spec = importlib.util.spec_from_file_location(file.stem, file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[file.stem] = module
            spec.loader.exec_module(module)

            parser, custom_settings = module.Tool.getArgumentParser()

            # Create the desired dictionary
            result_dict = convert_parser_to_dict(parser, custom_settings)
            convert_script(file, result_dict)
