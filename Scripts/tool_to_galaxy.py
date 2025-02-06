import xml.etree.ElementTree as ET
from pathlib import Path

def tool_to_galaxy_xml(tool):
    tool_elem = ET.Element("tool", id=tool.name.lower().replace(" ", "_"), name=tool.name, version="1.0")
    description = ET.SubElement(tool_elem, "description")
    description.text = tool.description
    
    requirements = ET.SubElement(tool_elem, "requirements")
    for dep in tool.dependencies.get("pip", []):
        package = ET.SubElement(requirements, "package", version=dep.split("==")[-1])
        package.text = dep.split("==")[0]
    
    command = ET.SubElement(tool_elem, "command", detect_errors="exit_code")
    command.text = "python script.py "
    for inp in tool.inputs:
        command.text += f"{inp['names'][1]} \${{input_{inp['names'][1][2:]}}} "
    for out in tool.outputs:
        command.text += f"{out['names'][1]} \${{output_{out['names'][1][2:]}}} "
    
    inputs = ET.SubElement(tool_elem, "inputs")
    for inp in tool.inputs:
        param = ET.SubElement(inputs, "param", name=f"input_{inp['names'][1][2:]}", type="text")
        param.set("label", inp["help"])
        if "default" in inp:
            param.set("value", str(inp["default"]))
        if "choices" in inp:
            param.set("type", "select")
            for choice in inp["choices"]:
                option = ET.SubElement(param, "option", value=choice)
                option.text = choice
    
    outputs = ET.SubElement(tool_elem, "outputs")
    for out in tool.outputs:
        data = ET.SubElement(outputs, "data", name=f"output_{out['names'][1][2:]}", format="txt")
        data.set("label", out["help"])
    
    return ET.tostring(tool_elem, encoding='unicode')


class Tool:

    categories = ['Segmentation']
    dependencies = dict(conda=[], pip=['cellpose==3.1.0', 'pandas==2.2.2'])
    environment = 'cellpose'
    test = ['--input_image', 'img02.png', '--segmentation', 'img02_segmentation.png', '--visualization', 'img02_segmentation.npy']
    modelType = None
    
    name = "Cellpose"
    description = "Segment cells with cellpose."
    inputs = [
            dict(
                names = ['-i', '--input_image'],
                help = 'The input image path.',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['-m', '--model_type'],
                help = 'Model type. “cyto”=cytoplasm model; “nuclei”=nucleus model; “cyto2”=cytoplasm model with additional user images; “cyto3”=super-generalist model.',
                default = 'cyto',
                choices = ['cyto', 'nuclei', 'cyto2', 'cyto3'],
                type = str,
            ),
            dict(
                names = ['-g', '--use_gpu'],
                help = 'Use GPU (default is CPU).',
                default = False,
                type = bool,
            ),
            dict(
                names = ['-a', '--auto_diameter'],
                help = 'Automatically estimate cell diameters, see https://cellpose.readthedocs.io/en/latest/settings.html.',
                default = False,
                type = bool,
            ),
            dict(
                names = ['-d', '--diameter'],
                help = 'Estimate of the cell diameters (in pixels).',
                default = 30,
                type = int,
            ),
            dict(
                names = ['-c', '--channels'],
                help = 'Channels to run segementation on. For example: "[0,0]" for grayscale, "[2,3]" for G=cytoplasm and B=nucleus, "[2,1]" for G=cytoplasm and R=nucleus.',
                default = '[0,0]',
                type = str,
            ),
    ]
    outputs = [
            dict(
                names = ['-s', '--segmentation'],
                help = 'The output segmentation path.',
                default = '{input_image.stem}_segmentation.png',
                type = Path,
            ),
            dict(
                names = ['-v', '--visualization'],
                help = 'The output visualisation path.',
                default = '{input_image.stem}_visualization.npy',
                type = Path,
            ),
    ]
    
# Example usage
xml_output = tool_to_galaxy_xml(Tool)
print(xml_output)
