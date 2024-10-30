import sys
import argparse
from pathlib import Path

class Tool:

    # Taken from https://py.imagej.net/en/latest/Puncta-Segmentation.html
    categories = ['Fiji', 'Registration']
    dependencies = dict(conda=['conda-forge::openjdk=11'], pip=[])
    additionalInstallCommands = dict(all=[], 
                                     windows=[f'Set-Location -Path "{Path(__file__).parent.resolve()}"',
                                              f'Invoke-WebRequest -URI https://downloads.imagej.net/fiji/releases/2.14.0/fiji-2.14.0-win64.zip -OutFile fiji.zip',
                                              f'Expand-Archive -Force fiji.zip',
                                              f'Remove-Item fiji.zip'
                                              f'Copy-Item "{(Path(__file__).parent / "StackReg").resolve()}" -Destination "{Path('Fiji.app/plugins').resolve()}"'],
                                     linux=[f'cd {Path(__file__).parent.resolve()}',
                                            'wget https://downloads.imagej.net/fiji/releases/2.14.0/fiji-2.14.0-linux64.zip',
                                            'unzip -o fiji-2.14.0-linux64.zip',
                                            'rm fiji-2.14.0-linux64.zip',
                                            f'cp -a {Path(__file__).parent.resolve()}/StackReg/. ./Fiji.app/plugins'], 
                                     mac=['export DYLD_LIBRARY_PATH="/usr/local/lib/"',
                                            f'cd {Path(__file__).parent.resolve()}',
                                            'wget https://downloads.imagej.net/fiji/releases/2.14.0/fiji-2.14.0-macosx.zip',
                                            'unzip -o fiji-2.14.0-macosx.zip',
                                            'rm fiji-2.14.0-macosx.zip',
                                            f'cp -a {Path(__file__).parent.resolve()}/StackReg/. ./Fiji.app/plugins'])
    environment = 'fiji'
    
    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("StackReg", description="Stack registration with the StackReg Fiji plugin.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-t', '--transformation', help='The transformation applied on each slice.', choices=['Translation', 'Rigid Body', 'Scaled rotation', 'Affine'], type=str)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image path.', default='{input_image.stem}_stackreg.{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit('Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Run Fiji macro')
        import subprocess
        import platform
        fijiPath = str(Path(__file__).parent.resolve() / 'Fiji.app') if platform.system() == 'Darwin' else 'fiji' if platform.system() == 'Linux' else 'Fiji.exe'
        macroPath = str(Path(__file__).parent.resolve() / 'StackReg' / 'stackreg.ijm')
        return subprocess.run([fijiPath, '--headless', '--console', '-macro', macroPath, f'[{args.input},{args.transformation},{args.output}]'])
        

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)