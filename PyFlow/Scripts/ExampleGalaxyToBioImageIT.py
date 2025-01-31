# Warning: the following is far from being finalized




import xml.etree.ElementTree as ET
from pathlib import Path

def parse_tool_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract basic tool metadata
    tool_id = root.attrib.get('id', 'UnknownTool')
    tool_name = root.attrib.get('name', 'Unknown Tool')
    version = root.attrib.get('version', '1.0')

    # Extract requirements
    requirements = root.find('requirements/package')
    conda_package = requirements.text.strip() if requirements is not None else ""
    python_version = requirements.attrib.get('python', '')

    # Extract command details
    command = root.find('command').text.strip().replace('${', '{')
    default_args = command.replace('true', 'True').replace('false', 'False')

    # Parse inputs
    inputs = []
    for param in root.findall('inputs/param'):
        param_dict = {
            'name': param.attrib['name'],
            'type': param.attrib.get('type', 'str'),
            'argument': param.attrib.get('argument', None),
            'default': param.attrib.get('value', None),
            'help': param.attrib.get('help', ''),
            'choices': [opt.attrib['value'] for opt in param.findall('option')]
        }
        inputs.append(param_dict)

    # Parse outputs
    output = root.find('outputs/data')
    output_name = output.attrib['name']
    output_format = output.attrib.get('format', '')

    return {
        'tool_id': tool_id,
        'tool_name': tool_name,
        'version': version,
        'conda_package': conda_package,
        'python_version': python_version,
        'command': default_args,
        'inputs': inputs,
        'output_name': output_name,
        'output_format': output_format
    }

def generate_python_class(tool_data):
    # Python class template with parsed details
    class_template = f"""
import argparse
from pathlib import Path
import subprocess

class Tool:

    categories = ['Sairpico', 'Deconvolution']
    dependencies = dict(python='{tool_data['python_version']}', conda=['{tool_data['conda_package']}'], pip=[])
    environment = 'simglib'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("{tool_data['tool_name']}", description="{tool_data['tool_name']} tool generated from XML.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
    """

    # Generate input argument parsers
    for param in tool_data['inputs']:
        param_type = 'Path' if param['type'] == 'data' else 'int' if param['type'] == 'integer' else 'float' if param['type'] == 'float' else 'str'
        default = f", default={param['default']}" if param['default'] else ""
        choices = f", choices={param['choices']}" if param['choices'] else ""
        required = 'required=True' if not param['default'] else ""
        argument = f'"{param["argument"]}"' if param["argument"] else ""
        help_text = param['help']

        class_template += f"""
        inputs_parser.add_argument("--{param['name']}", type={param_type}, help="{help_text}", {required}{default}{choices})
    """

    # Generate output argument parser
    class_template += f"""
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='The output denoised image path.', default='{tool_data['output_name']}.tiff', type=Path)
        return parser, dict(input_image=dict(autoColumn=True))

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print('Performing {tool_data['tool_name']}')
        commandArgs = [
            {tool_data['command']}
        ]
        return subprocess.run([str(ca) for ca in commandArgs])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    # or
	# parser = create_parser(module.Tool)
    args = parser.parse_args()
    tool.processData(args)
    """
    return class_template

def save_to_file(class_code, output_file):
    with open(output_file, 'w') as f:
        f.write(class_code)

if __name__ == "__main__":
    xml_file = "tool.xml"  # Replace with your XML file path
    output_file = "generated_tool.py"

    tool_data = parse_tool_xml(xml_file)
    class_code = generate_python_class(tool_data)
    save_to_file(class_code, output_file)

    print(f"Python class generated and saved to {output_file}")
