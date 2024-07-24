import argparse
import json
import pandas
from pathlib import Path

parser = argparse.ArgumentParser('NF List files', description='Create a data frame form files.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--input_path', '-ip', help='The input path', required=True)
parser.add_argument('--column_name', '-nn', help='The column name (nodename_path or custom column name)', required=True)
parser.add_argument('--output_path', '-op', help='The output folder path', required=True)

args = parser.parse_args()

data = pandas.DataFrame()
path = Path(args.input_path)
data[args.column_name] = [str(p) for p in sorted(list(path.iterdir()))] if path.is_dir() else [str(path)]

data.to_csv(args.output_path, index=False)