import re
import json
from pathlib import Path

def parse_arguments(arg_parser_content):
    """Parse arguments from the given content of argument groups."""
    args_pattern = re.compile(r'add_argument\((.*?)\)', re.DOTALL)
    arguments = []
    for match in args_pattern.finditer(arg_parser_content):
        arg_str = match.group(1)

        # Extract flags
        flags_match = re.findall(r'\s*"([^"]+)"', arg_str.split(',', 1)[0])
        flags = flags_match if flags_match else []

        # Extract help text
        help_match = re.search(r'help="(.*?)"', arg_str)
        help_text = help_match.group(1) if help_match else ""

        # Extract type
        type_match = re.search(r'type=(\w+)', arg_str)
        type_value = type_match.group(1) if type_match else "str"
        if type_value == "Path":
            type_value = Path
        elif type_value == "int":
            type_value = int
        elif type_value == "bool":
            type_value = bool
        elif type_value == "float":
            type_value = float
        elif type_value == "str":
            type_value = str
        else:
            raise Exception('Unimplemented type')

        # Extract default value
        default_match = re.search(r'default=([\w"\[\]]+)', arg_str)
        default_value = eval(default_match.group(1)) if default_match else None

        # Extract required flag
        required_match = re.search(r'required=(True|False)', arg_str)
        required = required_match.group(1) == "True" if required_match else False

        # Handle store_true and store_false
        if "store_true" in arg_str:
            type_value = bool
            default_value = True
        elif "store_false" in arg_str:
            type_value = bool
            default_value = False

        # Build argument dict
        argument = {
            "flags": flags,
            "help": help_text,
            "type": type_value,
        }
        if required:
            argument["required"] = True
        if default_value is not None:
            argument["default"] = default_value

        arguments.append(argument)

    return arguments

def convert_script(script_path):
    with open(script_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Extract the content before the getArgumentParser function
    before_gap_match = re.search(r'(.*?)(?=def getArgumentParser\(.*?\):)', content, re.DOTALL)
    before_gap = before_gap_match.group(0) if before_gap_match else content

    # Extract the content after the getArgumentParser function
    after_gap_match = re.search(r'return parser, dict(.*?)', content, re.DOTALL)
    after_gap = after_gap_match.group(0) if after_gap_match else content

    # Extract getArgumentParser function content
    get_arg_parser_match = re.search(r'def getArgumentParser\(.*?\):(.+?)\n\s{4}return', content, re.DOTALL)
    arg_parser_content = get_arg_parser_match.group(1) if get_arg_parser_match else ""

    # Extract the description
    match_desc = re.search(r'argparse\.ArgumentParser\("(.*?)", description="(.*?)"', arg_parser_content)
    name = match_desc.group(1) if match_desc else "Unknown"
    description = match_desc.group(2) if match_desc else "No description."

    # Define groups and match their sections
    groups = {
        "inputs": None,
        "advanced": None,
        "outputs": None
    }
    
    # Match each group within the function content
    for group in groups.keys():
        group_match = re.search(rf'{group}_parser = .*?add_argument_group\(.*?\)\s*(.+?)(\n\s*\n|$)', arg_parser_content, re.DOTALL)
        if group_match:
            groups[group] = parse_arguments(group_match.group(1))
    
    # Construct new script content
    new_content = f"""
class Tool:
    name = "{name}"
    description = "{description}"

    inputs = {json.dumps(groups['inputs'], indent=4, default=str)}

    advanced = {json.dumps(groups['advanced'], indent=4, default=str)}

    outputs = {json.dumps(groups['outputs'], indent=4, default=str)}
"""

    # Combine the unchanged part and new content
    result_content = before_gap + new_content + after_gap

    # Write the new content
    with open(script_path, "w", encoding="utf-8") as file:
        file.write(result_content)

base_dir = "/Users/amasson/Travail/bioimageit/PyFlow/Tools"

for tool_folder in sorted(list(Path(base_dir).iterdir())):
    if not tool_folder.is_dir(): continue
    for file in sorted(list(tool_folder.iterdir())):
        if file.suffix == ".py":
            convert_script(file)
