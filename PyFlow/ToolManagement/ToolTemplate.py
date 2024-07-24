from importlib import import_module
import argparse

class Tool():

    categories = ['Custom']
    environment = 'environmentName'
    # List your tool dependencies:
    # - the python version
    # - the conda packages which will be installed with 'conda install packageName'
    # - the pip packages which will be installed with 'pip install packageName'
    dependencies = dict(python=3.10, conda=[], pip=[])

    # Describe the tool inputs & outputs with ArgumentParser
    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Tool name", description="Tool description", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        # inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        outputs_parser = parser.add_argument_group('outputs')
        # outputs_parser.add_argument('-o', '--out', help='The output mask path.', default='{input_image}_segmentation.png', type=Path)
        return parser

    # Initialize your tool
    def initialize(self, args):
        print('Loading libraries...')
        # Import your models
        # For example
        # self.models = import_module('cellpose.models')
    
    # Process the data frame
    def processDataFrame(self, dataFrame):
        return dataFrame
    
    # Process the data
    def process(self, args):
        return

if __name__ == "__main__":
    # When this script is called directly: instanciate the tool, parse the arguments and launch the processing
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)