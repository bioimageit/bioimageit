import pandas
class Tool():
    
    # The display name
    name = "Tool name"
    # The tool description is important for the user to understand what the tool does
    description = "Tool description."
    # The category which defines where the tool will apear in the tool library (the Tools tab)
    categories = ['Workflow']
    # The name of the conda environment which will be used to run the tool
    # It will be created when needed unless the BioImageIT environment does not satisfy the requirements 
    # (in this case the tool we be run in the BioImageIT environment)
    # You can set it to BioImageIT if you are sure the tool only requires packages installed with BioImageIT 
    environment = 'environmentName'
    # The tool dependencies:
    # - the python version
    # - the conda packages which will be installed with 'conda install packageName'
    # - the pip packages which will be installed with 'pip install packageName'
    dependencies = dict(python='==3.10', conda=[], pip=[])
    # The inputs
    inputs = [dict(name='input_image', help='The input image path.', 
                   required=True, type='Path', autoColumn=True)]
    outputs = [dict(name='output_image', help='The output image.', 
                    default='{input_image.stem}_detections{input_image.exts}', type='Path')]
    
    # Merge the input DataFrames (optional)
    def mergeDataFrames(self, dataFrames, argsList):
        if len(dataFrames)==0: return pandas.DataFrame()
        result = pandas.concat(dataFrames, axis=1)
        # Remove duplicated columns
        result = result.loc[:,~result.columns.duplicated()].copy()
        # Replace every NaN with the first non-NaN value in the same column above it.
        # propagate[s] last valid observation forward to next valid
        result = result.ffill()
        return result
    
    # Process the DataFrame (optional)
    def processDataFrame(self, dataFrame, argsList):
        return dataFrame
    
    # Process the entire DataFrame
    def processAllData(self, argsList):
        return 
    
    # Process one row of the input DataFrame
    def processData(self, args):
        return
    

