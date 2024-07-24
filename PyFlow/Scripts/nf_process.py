import argparse
import json
import pandas
from pathlib import Path

import bioimageit_core.api as iit
from bioimageit_formats import FormatsAccess

# Todo: common execution file for RunTool and nf_process (just need to update progression bar and handle no dataFrame)

parser = argparse.ArgumentParser('NF Process', description='Executes a node.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--data_frame', '-df', help='The input data frame path (.csv file)', required=True)
parser.add_argument('--node_description', '-nd', help='The node description path (.json file)', required=True)
parser.add_argument('--node_parameters', '-np', help='The node parameters path (.json file)', required=True)
# parser.add_argument('--formats_file', '-ff', help='The formats file path (.json file)', required=True)
parser.add_argument('--config_file', '-cf', help='The config file path (.json file)', required=True)
parser.add_argument('--output_path', '-op', help='The output folder path', default=Path())

args = parser.parse_args()

req = iit.Request(args.config_file)
req.connect()

dataFrame = pandas.read_csv(args.data_frame)

with open(args.node_description, 'r') as f:
    nodeDescription = json.load(f)

with open(args.node_parameters, 'r') as f:
    nodeParameters = json.load(f)

# with open(args.formats_file, 'r') as f:
#     formats = json.load(f)

# def getFormatExtension(formats, format):
#     for fname, info in formats.items():
#         if fname == format:
#             return info['extension']

def getOutputFilePath(info, nodeDescription, index=None):
    nodeName = nodeDescription['node_name']
    outputPath = nodeDescription['workflow_path']
    indexPrefix = f'_{index}' if index is not None else ''
    # return Path(outputPath).resolve() / nodeName / f'{info["name"]}{indexPrefix}.{getFormatExtension(formats, info["type"])}'
    return Path(outputPath).resolve() / nodeName / f'{info["name"]}{indexPrefix}.{FormatsAccess.instance().get(info["type"]).extension}'

def getColumnName(nodeName, output):
    return nodeName + '_' + output['name']

def setOutputs(nodeDescription, dataFrame):
    for output in nodeDescription['outputs']:
        dataFrame[getColumnName(nodeDescription['node_name'], output)] = [getOutputFilePath(output, nodeDescription, i) for i in range(len(dataFrame))]
    
def getArgs(nodeDescription, nodeParameters, dataFrame):
    # "Compute" = initialize output paths in the dataframe, since the node was not necessarily computed before
    for output in nodeDescription['outputs']:
        columnName = getColumnName(nodeDescription['node_name'], output)
        if columnName not in dataFrame.columns:
            dataFrame[columnName] = [getOutputFilePath(output, nodeDescription, i) for i in range(len(dataFrame))]
    argsList = []
    for index, row in dataFrame.iterrows():
        args = {}
        for parameterName, parameterDict in nodeParameters.items():
            args[parameterName] = str(parameterDict['value'] if parameterDict['type'] == 'value' else row[parameterDict['columnName']])
        for output in nodeDescription['outputs']:
            outputPath = Path(dataFrame.at[index, getColumnName(nodeDescription['node_name'], output)])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            args[output['name']] = str(outputPath)
        argsList.append(args)
    return argsList

def execute(nodeDescription, nodeParameters, dataFrame, outputFolder, req):

    toolId = nodeDescription['id']
    toolVersion = nodeDescription['version']
    tool = req.get_tool(f'{toolId}_v{toolVersion}')

    argsList = getArgs(nodeDescription, nodeParameters, dataFrame)
    argsList = argsList if type(argsList) is list else [argsList]

    setOutputs(nodeDescription, dataFrame)
    
    outputFolder.mkdir(exist_ok=True, parents=True)
    
    job_id = req.new_job()
    try:
        req.runner_service.set_up(tool, job_id)
        for args in argsList:
            preparedArgs = req._prepare_command(tool, args)
            req.runner_service.exec(tool, preparedArgs, job_id)
        # preparedArgs = [req._prepare_command(tool, args) for args in argsList]
        # req.runner_service.exec_multi(tool, preparedArgs, job_id, outputFolder)
        req.runner_service.tear_down(tool, job_id)
    except Exception as err:
        req.notify_error(str(err), job_id)

    dataFrame.to_csv(outputFolder / 'output_data_frame.csv', index=False)

    with open(outputFolder / 'args_list.json', 'w') as f:
        json.dump(argsList, f)

execute(nodeDescription, nodeParameters, dataFrame, Path(args.output_path), req)