# Tool integration and creation

## Data flow

BioImageIT propagates data in the workflow with DataFrames. The DataFrames describe the data of the Workflow and points to associated data files.
The DataFrames are sent from nodes to nodes, each node extends the incoming DataFrames or generate new ones to contribute to the objective of the workflow.
The DataFrames are updated when the user creates and modify the workflow. This enables users to see how the data will evolve through the workflow. 
The data described by the DataFrames is processed when the user executes the workflow.
When a node is updated (user selects it or changes its parameters) or executed, each DataFrame row is processed to provide the arguments of the node:
- the "Column" parameters are set to the value of the current row at their corresponding columns,
- the "Constant" parameters are fixed for all rows.

Let's take a simple workflow: a "List files" node connected to a "Cellpose_segmentation" node.
The `folderPath` parameter of the "List files" node is set to a folder containing 4 images. The `input_image` parameter of the "Cellpose_segmentation" node is set to the `path` column, and the other parameters are let by default (`{"model_type": "cyto", "use_gpu": False, "auto_diameter": False, "diameter": 30, "channels": [0,0]}`).

The "List files" node will generate a DataFrame with a single column "path", and 4 rows, one for each image.
This DataFrame is sent to the "Cellpose_segmentation" node which will extend it with an "Cellpose_segmentation: output_segmentation" column 
describing where the output images will be saved.
The thumbnails of existing images will be generated, but the output images will not be visible yet since they do not exist.

It's only when the user executes the workflow that the "Cellpose_segmentation" node will generate the outputs. 
More precisely, the processData() of the "Cellpose_segmentation" node will be called once for each row.
The args argument of the processData() is generated from the current row of the DataFrame (the value of the "path" column at the current row for the `input_image` argument) and the constant rameters of the node for the other arguments (`{"model_type": "cyto", "use_gpu": False, "auto_diameter": False, "diameter": 30, "channels": [0,0]}`).
BioImageIT will generate the thumbnails at the end of the node execution.

## Update methods and processing methods

BioImageIT will call mergeDataFrames() then processDataFrame() when the node is clicked or one of its parameter is modified.
Those *update methods* process the DataFrames.
- mergeDataFrames() merges the input DataFrames into a single one which will be used by the next methods
- processDataFrame() generates a new DataFrames or modify the input DataFrame, using the node parameters
Those methods must be executed in a short time since they are called when the user interacts with the workflow.

The time consuming processing happens when the user executes the workflow (a dialog shows the execution progression and prevents interactions).
At execution time, the *update methods* are called again, followed by calls to the *processing methods*: processAllData() and then processData(). 
Those methods process the data described by the DataFrames:
- processAllData() processes the data described by the entire DataFrame
- processData() processed the data described by a single row of the DataFrame
processData() is the most commonly used method. 
In our example, each image is described by a row, so the "Cellpose_segmentation" tool just need to implement the processData() to process all images.
processAllData() is usefull to process all data at once. 
For example, this is necessary for the Omero upload node to open a connection to the Omero database once for all items (and not open and close connection for each DataFrame row). It is also used by the "ExoDeepFinder train" node to train a model from all data described by the final DataFrame.

### The output message

The `self.outputMessage` can be set in the *update and processing methods* to display a message to the user in the DataFrame view. This is used by the `label_statistics` tool to explain that the DataFrame is empty during the workflow creation and will be updated only once the workflow is executed. The processDataFrame() just sets the `self.outputMessage` to "Label statistics will be computed on execution.". Then, the processData() method resets this `self.outputMessage` to an empty string since the DataFrame will be generated and visible.

## Custom tools

Integrating existing tools and creating new ones is quite easy in BioImageIT. It's just about creating one python script which defines the tool.

Click the "Create tool" button in the "Tools" tab. Enter a name and click "OK". This will create a definition file for the tool and open it in a code editor (defined in the Preferences > "External code editor"). Then just modify this file to fit your needs and save it. It will appear in the tool list ("Tools" tab) for you to create new nodes.

`PyFlow/Tools/SimpleITK/label_statistics.py` returns one DataFrame per row.

Can define `outputMessage` to display something in the DataTable.

```python
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
    # A dependency can either by a string (of the form channel::packageName==version.nuber, channel and version.number being optional, version.number being very much encouraged) or a dictionnary with the attributes `name`, `platforms`, `optional`, `dependencies` as defined in the [Wetlands dependencies documentation](https://arthursw.github.io/wetlands/latest/dependencies/)
    dependencies = dict(python='==3.10', conda=['conda-forge::openjdk=11'], pip=['numpy==2.2'])
    # The inputs of the tools
    inputs = [dict(
                name = 'input_image',               # Name of the input
                help = 'The input image path.',     # Description of the input which appears as a tooltip
                required = True,                    # Whether the input is required to execute the tool
                type = 'Path',                      # Type of the input, can be 'Path', 'bool', 'str', 'int', 'float' (as the Python types)
                autoColumn = True,                  # Whether the parameter is automatically assigned to a column of the input dataFrame
            ),
            dict(
                name = 'separate',
                help = 'Split RGB images into separate channels.',
                default = False,                    # The default value of the input
                type = 'bool',
                advanced = True,                    # Whether the parameter appears in the default input tab or advanced tab
            ),
            dict(
                name = 'compression',
                help = 'Specify the codec to use when saving images.',
                default = '',
                choices = ['', 'Uncompressed', 'LZW', 'JPEG-2000', 'JPEG-2000 Lossy', 'JPEG', 'zlib'],  # The possible values for the parameter. This will create a dropdown menu in the GUI
                type = 'str',
                advanced = True,
            ),
            dict(
                name = 'columnName',
                help = 'Column name',
                type = 'str',
                default = 'values',
                static = True,          # The input is always constant, cannot be set to column
            ),
            dict(
                name = 'p_value',
                shortname = 'pval',
                help = 'P-value to account for the probability of false detection.',
                default = 0.001,
                decimals = 6,
                type = 'float',          # The number of decimals this value can take (for the Qt spin box input)
            ),
        ]
    # The outputs of the tools
    outputs = [dict(name='output_image', help='The output image.', 
                    default='{input_image.stem}_detections{input_image.exts}', type='Path')]
    
    # Merge the input data frames (optional)
    # Arguments:
    # - dataFrames: the input DataFrames of the node
    # - argsList: the list of arguments generated from each row of the DataFrame (each DataFrame row is converted to a list of arguments for the node)
    # By default, BioImageIT concatenates all input DataFrames into a single one, 
    # removes duplicated columns, and replaces every NaN 
    # with the first non-NaN value in the same column above it (propagates last valid observation forward to next valid).
    # It returns an empty DataFrame if there are no input DataFrame.
    # Reimplement this method to override the default behavior.
    # It must return a single DataFrame which will be used as the input DataFrame for the next methods
    # def mergeDataFrames(self, dataFrames, argsList):
    #     return pandas.concat(dataFrames, axis=1) if len(dataFrames)>0 else return pandas.DataFrame() # (simplified) example implementation
    
    # Process the DataFrame (optional)
    # Arguments:
    # - dataFrames: the input DataFrame of the node (more precisely, the output of the mergeDataFrames() method)
    # - argsList: the list of arguments generated from the DataFrame rows (and constant node parameters)
    # This method is called any time the user clicks on a node or updates its parameter
    # and when the workflow is executed or exported.
    # 
    # By default, BioImageIT simply returns a clone of the input DataFrame, 
    # but this behavior can be modified by implementing this function.
    # This is how nodes like "List files", "ColumnRegex" or "Merge" work: they modify the input DataFrame(s) or generate a new one
    # 
    # After processDataFrame, BioImageIT will do the following steps:
    # - if this resulting DataFrame is empty, create a new one from its input parameters
    # - otherwise, augment the DataFrame by adding one column per output
    # - display the ouputMessage if it was defined in processDataFrame
    # - send the DataFrame to the next node
    # - and finally, generate the preview thumbnails from the image paths in the DataFrame (if any)
    def processDataFrame(self, dataFrame, argsList):
        return dataFrame
    
    # Process all Data associated with the DataFrame
    # Argument:
    # - argsList: the list of arguments generated from the DataFrame rows (and constant node parameters)
    # 
    # This method can optionnaly return a list of DataFrames which will be concatenated and sent to the node output after execution.
    def processAllData(self, argsList):
        return 
    
    # Process one row of the input DataFrame
    # Argument:
    # - args: the arguments generated from the current row of the DataFrame (and constant node parameters)
    #
    # This method can optionnaly return a DataFrame which will overwrite the DataFrame returned by processAllData() for the current row.
    # The DataFrames resulting of all processData() calls will be concatenated and sent to the node output after execution. 
    # This behavior is used by the label_statistics and label_overlaps nodes.
    def processData(self, args):
        return
    

```