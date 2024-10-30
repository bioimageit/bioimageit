import sys
import argparse
from pathlib import Path

class Tool:

    # Taken from https://py.imagej.net/en/latest/Puncta-Segmentation.html
    categories = ['Fiji', 'Registration']
    dependencies = dict(conda=['conda-forge::pyimagej==1.5.0', 'conda-forge::openjdk=11'], pip=[])
    additionalInstallCommands = dict(all=[], linux=[], mac=['export DYLD_LIBRARY_PATH="/usr/local/lib/"'])
    environment = 'pyimagej'
    
    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("StackReg", description="Stack registration with the StackReg Fiji plugin.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-t', '--transformation', help='The transformation applied on each slice.', choices=['Translation', 'Rigid Body', 'Scaled rotation', 'Affine'], type=str)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image path.', default='{input_image.stem}_stackreg.{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )

    def initialize(self, args):
        print('Loading libraries...')
        import imagej
        import scyjava

        pluginsPath = Path(__file__).parent / 'StackReg'
        scyjava.config.add_option(f'-Dplugins.dir={pluginsPath.resolve()}')

        # initialize imagej
        self.ij = imagej.init('sc.fiji:fiji:2.15.0', mode='headless')
        print(f"ImageJ version: {self.ij.getVersion()}")

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit('Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)

        print(f'[[1/3]] Load image {input_image}')
        # load test data
        image = self.ij.io().open(input_image)
        image = self.ij.op().convert().int32(image) # convert image to 32-bit

        # convert ImgPlus to ImagePlus
        image = self.ij.py.to_imageplus(image)

        print(f'[[2/3]] Process image')
        # run the analyze particle plugin
        self.ij.py.run_plugin(plugin="StackReg ", args=f"transformation=[{args.transformation}]", imp=image)

        print(f'[[3/3]] Save image')
        self.ij.io().save(image, args.output_image)
        

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)