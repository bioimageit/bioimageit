from pathlib import Path
import argparse

class Tool():

    name = "Tool name"
    description = "Tool description."
    categories = ['Workflow']
    environment = 'environmentName'
    # List your tool dependencies:
    # - the python version
    # - the conda packages which will be installed with 'conda install packageName'
    # - the pip packages which will be installed with 'pip install packageName'
    dependencies = dict(python='==3.10', conda=[], pip=[])
    inputs = [
            dict(
                names = ['-i', '--input_image'],
                help = 'The input image path.',
                required = True,
                type = Path,
                autoColumn = True,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output_image'],
                help = 'The output image.',
                default = '{input_image.stem}_detections{input_image.exts}',
                type = Path,
            ),
    ]
    
    # Initialize your tool (optional)
    def initialize(self, args):
        print('Loading libraries...')
    
    # Process the data frame (optional)
    def processDataFrame(self, dataFrame, argsList):
        return dataFrame
    
    # Process the data
    def processData(self, args):
        return