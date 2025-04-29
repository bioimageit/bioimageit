from munch import DefaultMunch
from pathlib import Path

def type_name_to_type(type):
    if type.lower() == 'integer' or type == 'int':
        return 'int'
    elif type.lower() == 'string' or type == 'str':
        return 'str'
    elif type.lower() == 'float':
        return 'float'
    elif type.lower() == 'path':
        return 'Path'
    elif type.lower() == 'boolean' or type == 'bool':
        return 'bool'
    else:
        raise Exception('Not implemented')
    
def convert_munch_to_dict(munch_obj):
    converted = f"""
    name = "{munch_obj.info.fullname()}"
    description = "Auto-generated description."
    inputs = [
    """
    
    for input_item in munch_obj.info.inputs:
        entry = f"""        dict(
            names = ['--{input_item.name}'],
            help = '{input_item.description}',
            type = {type_name_to_type(input_item.type)},
"""
        if hasattr(input_item, "default_value"):
            entry += f"            default = {input_item.default_value},\n"
        if hasattr(input_item, "auto") and input_item.auto:
            entry += f"            autoColumn = True,\n"
        entry += "        ),\n"
        converted += entry
    
    converted += "    ]\n    outputs = [\n"
    
    for output_item in munch_obj.info.outputs:
        entry = f"""        dict(
            names = ['--{output_item.name}'],
            help = '{output_item.description}',
            type = {type_name_to_type(output_item.type)},
        ),\n"""
        converted += entry
    
    converted += "    ]\n"""
    return converted

# Example usage

tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'omero_download', inputs=[
        dict(name='image', description='Image to upload', type='string'),
        dict(name='metadata_columns', description='Metadata columns (for example ["column 1", "column 2"])', type='string'),
        dict(name='dataset_id', description='Dataset ID (ignored if negative)', type='integer'),
        dict(name='dataset_name', description='Dataset name', type='string'),
        dict(name='project_id', description='Project ID (optional, ignored if negative)', type='integer'),
        dict(name='project_name', description='Project name (optional)', type='string'),
    ], outputs=[])))

converted_string = convert_munch_to_dict(tool)
print(converted_string)



# from munch import DefaultMunch
# from pathlib import Path

# def convert_munch_to_dict(munch_obj):
#     converted = {
#         "name": munch_obj.info.fullname(),
#         "description": "Auto-generated description.",
#         "inputs": [],
#         "outputs": []
#     }
    
#     for input_item in munch_obj.info.inputs:
#         entry = {
#             "names": [f"--{input_item.name}"],
#             "help": input_item.description,
#             "type": eval(input_item.type) if input_item.type in ["int", "float", "str", "bool"] else Path,
#         }
#         if hasattr(input_item, "default_value"):
#             entry["default"] = input_item.default_value
#         if hasattr(input_item, "auto") and input_item.auto:
#             entry["autoColumn"] = True
#         converted["inputs"].append(entry)
    
#     for output_item in munch_obj.info.outputs:
#         entry = {
#             "names": [f"--{output_item.name}"],
#             "help": output_item.description,
#             "type": Path,
#         }
#         converted["outputs"].append(entry)
    
#     return converted


# tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'binary_threshold', inputs=[
#         dict(name='image1', description='Input image path', type='path', auto=True),
#         dict(name='channel', description='Channel to threshold', default_value=0, type='integer'),
#         dict(name='lowerThreshold', description='Lower threshold', default_value=0, type='integer'),
#         dict(name='upperThreshold', description='Upper threshold', default_value=255, type='integer'),
#         dict(name='insideValue', description='Inside value', default_value=1, type='integer'),
#         dict(name='outsideValue', description='Outside value', default_value=0, type='integer'),
#     ], outputs=[
#         dict(name='thresholded_image', description='Output image path', type='path'),
#     ])))

# converted_dict = convert_munch_to_dict(tool)
# print(converted_dict)