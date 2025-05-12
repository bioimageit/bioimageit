from pathlib import Path
import argparse
import shutil

parser = argparse.ArgumentParser(description="Transfert the test-data/ folders of all tools into one archive (if destination is not given) or in destination. If archive exists, the test-data will be taken from the given archive.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-s", "--source", help="Path to the source tools from which all test data will be copied", type=Path, default=Path(__file__).parent.parent / 'PyFlow' / 'Tools')
parser.add_argument("-a", "--archive", help="Path to the transfer folder in which all test data will be copied", type=Path, default="all-test-data")
parser.add_argument("-d", "--destination", help="Path to the destination source tools in which all test data will be copied. This arg must only be provided on the destination machine.", type=Path, default=None)
args = parser.parse_args()

source = args.archive if args.destination is not None and args.archive.exists() and args.archive.is_dir() else args.source
destination = args.archive if args.destination is None else args.destination
destination.mkdir(exist_ok=True, parents=True)

for tool in sorted(list(source.iterdir())):
    if not tool.is_dir(): continue
    tool_destination = destination / tool.name
    tool_destination.mkdir(exist_ok=True, parents=True)
    test_data = tool / 'test-data'
    if not test_data.exists(): continue
    shutil.copytree(test_data, tool_destination / 'test-data', dirs_exist_ok=True)