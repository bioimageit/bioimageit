import sys
from pathlib import Path
import subprocess
import argparse

parser = argparse.ArgumentParser('Remove signatures')
parser.add_argument('--app', help='Path to BioImageIT.app', required=True, type=Path)
args = parser.parse_args()

if not args.app.exists() or not args.app.is_dir():
    sys.exit(f'The path "{args.app}" does not exist or is not a directory.')

path = args.app.resolve()

files = sorted([path, path / 'Contents' / 'MacOS' / 'bioimageit', path / 'Contents' / 'Frameworks' / 'micromamba' / 'bin'/ 'micromamba'] + list(path.glob('**/*.so')) + list(path.glob('**/*.dylib')))

for f in files:
    print(f'Unsign {f}')
    subprocess.call(['codesign', '--remove-signature', f'{f}'])

subprocess.call(['codesign', '--check-notarization', '--verbose=4', f'{path}'])