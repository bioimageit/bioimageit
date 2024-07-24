import argparse
import json
import pandas
from pathlib import Path

parser = argparse.ArgumentParser('NF Process Data Frame', description='Read a csv file and a node description, and extends the csv with the node outputs.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--data_frame', '-df', help='The input data frame path (.csv file)', required=True)
parser.add_argument('--node_description', '-nd', help='The node description path (.json file)', required=True)
parser.add_argument('--formats_file', '-ff', help='The formats file path (.json file)', required=True)
parser.add_argument('--output_path', '-op', help='The output data frame path (.csv file)', required=True)

args = parser.parse_args()

data_frame = pandas.read_csv(args.data_frame)

with open(args.node_description, 'r') as f:
    node_description = json.load(f)

with open(args.formats_file, 'r') as f:
    formats = json.load(f)

def getFormatExtension(formats, format):
    for fname, info in formats.items():
        if fname == format:
            return info['extension']

def getOutputFilePath(info, node_description, index=None):
    nodeName = node_description.name
    outputPath = node_description.outputPath
    indexPrefix = f'_{index}' if index is not None else ''
    return Path(outputPath).resolve() / nodeName / f'{info['name']}{indexPrefix}.{getFormatExtension(formats, info['type'])}'

def getColumnName(nodeName, output):
    return nodeName + '_' + output.name

for output in node_description.outputs:
    data_frame[getColumnName(node_description.name, output)] = [getOutputFilePath(output, node_description, i) for i in range(len(data_frame))]