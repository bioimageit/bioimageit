import json
import SimpleITK as sitk
from PyFlow import getSourcesPath
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitToolNode import BiitToolNode

class SitkTool:
    def processData(self, args):
        # Replace Path inputs with the opened image or transform
        inputNameToType = {input['name']: input['type'] for input in self.inputs}
        for key, value in vars(args).items():
            if inputNameToType.get(key) == 'Path':
                setattr(args, key, sitk.ReadTransform(value) if str(value).endswith('.tfm') else sitk.ReadImage(value))
        
        inputs = [getattr(args, input['name']) for input in self.inputs]
        
        result = getattr(sitk, self.function_name)(*inputs)
        outputPath = getattr(args, self.outputs[0]['name'])
        if outputPath.suffix == '.tfm':
            sitk.WriteTransform(result, outputPath)
        else:
            sitk.WriteImage(result, outputPath)

def createSimpleITKNodes():

    with open(getSourcesPath() / 'Scripts' / 'simpleITK_functions.json', 'r') as f:
        tools = json.load(f)

    classes = {}
    for tool in tools.values():
        toolName = tool['name']
        rootName = 'sitk_' + (toolName.split(':')[0] if ':' in toolName else toolName)
        name = rootName
        i = 2
        while name in classes:
            name = rootName + '_' + str(i)
            i += 1
        functionName = tool['function_name']
        tool['categories'] = ['SimpleITK','All']
        tool['environment'] = 'bioimageit'
        tool['dependencies'] = dict()
        tool['moduleImportPath'] = ''
        for i in tool['inputs'] + tool['outputs']:
            i['help'] = ''
        
        inputNames = set([input['name'] for input in tool['inputs']])
        firstInputPath = next((input for input in tool['inputs'] if input['type'] == 'Path'), None)
        if firstInputPath is not None:
            firstInputPath['autoColumn'] = True
        firstInputPathName = firstInputPath['name'] if firstInputPath else None
        for output in tool['outputs']:
            if output['name'] in inputNames:
                output['name'] = 'out_' + output['name']
            if ('default' not in output):
                output['default'] = '{' + firstInputPathName + '.stem}_[index]{' + firstInputPathName + '.exts}' if firstInputPathName else ''
                # output['default'] = f'{{{firstInputPathName}.stem}_[index]{{{firstInputPathName}.exts}}'

        if hasattr(sitk, functionName):
            Tool = type('Tool_'+name, (SitkTool, ), tool)
            classes[name] = type(name, (BiitToolNode, ), dict(Tool=Tool))
        else:
            print(f'Warning: sitk has no {functionName} function.')

    return classes
