from importlib import import_module
import sys
import re
import json
from pathlib import Path

# def remove_quoted_content(s):
#     # Regular expression to match content between quotes '...' or "..."
#     cleaned_string = re.sub(r"(['\"])(.*?)\1", '', s)
#     return cleaned_string

# def parse_arguments(arg_parser_content):
#     """Parse arguments from the given content of argument groups."""
#     args_pattern = re.compile(r'add_argument\((.*?)\)', re.DOTALL)
#     arguments = []
#     for match in args_pattern.finditer(arg_parser_content):
#         arg_str = match.group(1)

#         # Extract flags
#         # Regular expression pattern to match strings that start with a word followed by '='
#         pattern = re.compile(r"^\s*\w+\s*=")
#         # Filter the list to keep only strings that do not match the pattern
#         positional_arguments = [arg for arg in arg_str.split(',') if not pattern.match(arg)]
#         flags = positional_arguments if positional_arguments else []

#         # Extract help text
#         help_match = re.search(r"help=['\"]([^'\"]*)['\"]", arg_str)
#         help_text = help_match.group(1) if help_match else ""

#         # Extract type
#         type_match = re.search(r'type=(\w+)', arg_str)
#         type_value = type_match.group(1) if type_match else "str"
#         if type_value == "Path":
#             type_value = Path
#         elif type_value == "int":
#             type_value = int
#         elif type_value == "bool":
#             type_value = bool
#         elif type_value == "float":
#             type_value = float
#         elif type_value == "str":
#             type_value = str
#         else:
#             raise Exception('Unimplemented type')

#         # Extract default value
#         default_match = re.search(r'default=([\w"\[\]]+)', arg_str)
#         default_value = eval(default_match.group(1)) if default_match else None

#         # Extract required flag
#         required_match = re.search(r'required=(True|False)', arg_str)
#         required = required_match.group(1) == "True" if required_match else False

#         # Handle store_true and store_false
#         if "store_true" in arg_str:
#             type_value = bool
#             default_value = True
#         elif "store_false" in arg_str:
#             type_value = bool
#             default_value = False

#         # Build argument dict
#         argument = {
#             "flags": flags,
#             "help": help_text,
#             "type": type_value,
#         }
#         if required:
#             argument["required"] = True
#         if default_value is not None:
#             argument["default"] = default_value

#         arguments.append(argument)

#     return arguments

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
            return value if isType else f'"{value}"'
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
    
    import ipdb ; ipdb.set_trace()

    # Extract the content before the getArgumentParser function
    before_gap_match = re.search(r'(.*?)(?=def getArgumentParser\(.*?\):)', content, re.DOTALL)
    before_gap = before_gap_match.group(0) if before_gap_match else content

    # Extract the content after the getArgumentParser function
    after_gap_match = re.search(r'return parser, dict[^\n]*(.*)', content, re.DOTALL)
    after_gap = after_gap_match.group(1) if after_gap_match else content

    # # Extract getArgumentParser function content
    # get_arg_parser_match = re.search(r'def getArgumentParser\(.*?\):(.+?)\n\s+return', content, re.DOTALL)
    # arg_parser_content = get_arg_parser_match.group(1) if get_arg_parser_match else ""

    # # Extract the description
    # match_desc = re.search(r'argparse\.ArgumentParser\("(.*?)", description="(.*?)"', arg_parser_content)
    # name = match_desc.group(1) if match_desc else "Unknown"
    # description = match_desc.group(2) if match_desc else "No description."

    # # Define groups and match their sections
    # groups = {
    #     "inputs": None,
    #     "advanced": None,
    #     "outputs": None
    # }
    
    # # Match each group within the function content
    # for group in groups.keys():
    #     group_match = re.search(rf'{group}_parser = .*?add_argument_group\(.*?\)\s*(.+?)(\n\s*\n|$)', arg_parser_content, re.DOTALL)
    #     # group_match = re.search(rf'{group}_parser = .*?add_argument_group', arg_parser_content, re.DOTALL)
    #     if group_match:
    #         groups[group] = parse_arguments(group_match.group(1))
    
    # Construct new script content
#     new_content =  f"""
#     name = "{tool_description['name']}"
#     description = "{tool_description['description']}"
#     inputs={dict_to_formatted_string(tool_description['inputs'])}

#     inputs = {json.dumps(tool_description['inputs'], indent=4, default=str)}

#     advanced = {json.dumps(tool_description['advanced'], indent=4, default=str)}

#     outputs = {json.dumps(tool_description['outputs'], indent=4, default=str)}
# """
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
            module = import_module(file.stem)
            parser, custom_settings = module.Tool.getArgumentParser()

            # Create the desired dictionary
            result_dict = convert_parser_to_dict(parser, custom_settings)
            convert_script(file, result_dict)
