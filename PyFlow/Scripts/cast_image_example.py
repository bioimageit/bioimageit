from pathlib import Path
import pandas
import SimpleITK as sitk
from PyFlow.Core.GraphManager import GraphManagerSingleton

# The compute function will be called when the user clicks the node
# Use it to modify the input data frame
def compute(self):
    data: pandas.DataFrame = self.getDataFrame()
    if not isinstance(data, pandas.DataFrame): return
    print('Compute data:')
    print(data)
    graphManager = GraphManagerSingleton().get()
    
    for index, row in data.iterrows():
        row['cellpose_out_uint8'] = Path(graphManager.workflowPath).resolve() / self.name / f'out_{index}.png'
    self.outArray.setData(data)

# The execute function will be called when the user clicks the execute button (from the tool bar)
# Use it to process the data files in the data frame
def execute(self):
    data = self.inArray.getData()
    print('Execute:')
    print(data)

    data: pandas.DataFrame = self.getDataFrame()
    outputData: pandas.DataFrame = self.outArray.currentData()
    for index, row in data.iterrows():
        inputImage = sitk.ReadImage(row['cellpose_out'])
        outputImage = sitk.Cast(inputImage, sitk.sitkUInt8)
        outputPath = Path(outputData.at[index, 'cellpose_out_uint8'])
        outputPath.parent.mkdir(exist_ok=True, parents=True)
        sitk.WriteImage(outputImage, outputPath)
    self.executed = True