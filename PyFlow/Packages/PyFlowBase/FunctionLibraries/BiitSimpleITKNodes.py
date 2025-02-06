from pathlib import Path
import json
import pandas
from munch import DefaultMunch
import SimpleITK as sitk

from PyFlow import getSourcesPath
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase
from PyFlow.invoke_in_main import inmain
from PyFlow.ThumbnailManagement.ThumbnailGenerator import ThumbnailGenerator

# import re

class SimpleITKBase(BiitArrayNodeBase):

    def __init__(self, name):
        super(SimpleITKBase, self).__init__(name)

    @classmethod
    def category(cls):
        return cls.tool.categories if hasattr(cls.tool, 'categories') else 'SimpleITK|Custom'
    
    def getFirstOuptutColumName(self):
        keys = list(self.parameters['outputs'].keys())
        outputName = keys[0]
        return self.getColumnName(outputName)
    
    def setOutputColumns(self, tool, data):
        for outputName, output in self.parameters['outputs'].items():
            for index, row in data.iterrows():
                # Guess output file extension: find the first input image format
                suffixes = '.tiff'
                for input in tool.inputs:
                    if input['type'] == Path and 'image' in input['name'] and self.getParameter(input['name'], row) is not None:
                        suffixes = ''.join(Path(self.getParameter(input['name'], row)).suffixes)
                        break
                data.at[index, self.getColumnName(outputName)] = self.getOutputDataFolderPath() / f'{outputName}_{index}{suffixes}'

    def execute(self):
        data: pandas.DataFrame|None = self.getDataFrame()
        if data is None:
            self.finishExecution()
            return
        outputData: pandas.DataFrame = self.outArray.currentData()
        for index, row in data.iterrows():
            argValues = []
            for input in self.tool.inputs:
                parameter = self.getParameter(input['name'], row)
                argValues.append(parameter if input['type'] != 'path' else sitk.ReadTransform(parameter) if str(parameter).endswith('.tfm') else sitk.ReadImage(parameter))
            # if 'vector' in inputImage.GetPixelIDTypeAsString():
            #     inputImage = inputImage.ToScalarImage()[self.getParameter('channel', row), :, :]
            result = self.__class__.sitkFunction(*argValues)
            outputPath = Path(outputData.at[index, self.getFirstOuptutColumName()])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            if outputPath.suffix == '.tfm':
                sitk.WriteTransform(result, outputPath)
            else:
                sitk.WriteImage(result, outputPath)
        self.finishExecution()
        return

class BinaryThreshold(SimpleITKBase):

    name = "Binary threshold"
    description = "SimpleITK Binary threshold."
    inputs = [
            dict(
            names = ['--image1'],
            help = 'Input image path',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--channel'],
            help = 'Channel to threshold',
            type = int,
            default = 0,
        ),
        dict(
            names = ['--lowerThreshold'],
            help = 'Lower threshold',
            type = int,
            default = 0,
        ),
        dict(
            names = ['--upperThreshold'],
            help = 'Upper threshold',
            type = int,
            default = 255,
        ),
        dict(
            names = ['--insideValue'],
            help = 'Inside value',
            type = int,
            default = 1,
        ),
        dict(
            names = ['--outsideValue'],
            help = 'Outside value',
            type = int,
            default = 0,
        ),
    ]
    outputs = [
        dict(
            names = ['--thresholded_image'],
            help = 'Output image path',
            type = Path,
        ),
    ]


    def __init__(self, name):
        super(BinaryThreshold, self).__init__(name)
    
    # def compute(self, *args, **kwargs):
    #     if not self.dirty: return
    #     data: pandas.DataFrame = self.getDataFrame()
    #     if isinstance(data, pandas.DataFrame):
    #         data = data.copy()
    #     else:
    #         return
    #     data[self.name + '_thresholded_image'] = [getOutputFilePath(self.__class__.tool.info.outputs[0], self.name, i) for i in range(len(data))]
    #     self.outArray.setData(data)
    #     self.outArray.setClean()
    #     self.dirty = False

    def execute(self):
        data: pandas.DataFrame|None = self.getDataFrame()
        if data is None:
            self.finishExecution()
            return
        outputData: pandas.DataFrame = self.outArray.currentData()
        for index, row in data.iterrows():
            args = ['image1', 'lowerThreshold', 'upperThreshold', 'insideValue', 'outsideValue']
            argValues = {}
            for arg in args:
                argValues[arg] = self.getParameter(arg, row)
            inputImage = sitk.ReadImage(argValues['image1'])
            if 'vector' in inputImage.GetPixelIDTypeAsString():
                inputImage = inputImage.ToScalarImage()[self.getParameter('channel', row), :, :]
            thresholdedImage = sitk.BinaryThreshold(inputImage, argValues['lowerThreshold'], argValues['upperThreshold'], int(argValues['insideValue']), int(argValues['outsideValue']))
            outputPath = Path(outputData.at[index, self.getFirstOuptutColumName()])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            sitk.WriteImage(thresholdedImage, outputPath)
        self.finishExecution()
        return
    
class AddScalarToImage(SimpleITKBase):

    name = "add_scalar_to_images"
    description = "Add a scalar value to all image values."
    inputs = [
            dict(
            names = ['--image'],
            help = 'Input image',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--value'],
            help = 'Value to add',
            type = int,
            default = 50,
        ),
    ]
    outputs = [
        dict(
            names = ['--out'],
            help = 'Output image',
            type = Path,
        ),
    ]

    def __init__(self, name):
        super(AddScalarToImage, self).__init__(name)

    # def execute(self):
    #     data: pandas.DataFrame = self.getDataFrame()
    #     outputData: pandas.DataFrame = self.outArray.currentData()
    #     for index, row in data.iterrows():
    #         inputImage = sitk.ReadImage(self.getParameter('image', row))
    #         resultImage = sitk.Add(inputImage, self.getParameter('value', row))
    #         outputPath = Path(outputData.at[index, self.name + '_out'])
    #         outputPath.parent.mkdir(exist_ok=True, parents=True)
    #         sitk.WriteImage(resultImage, outputPath)
    #     self.finishExecution()
    #     return
    
class ExtractChannel(SimpleITKBase):

    name = "extract_channel"
    description = "Extract an image channel."
    inputs = [
            dict(
            names = ['--image'],
            help = 'Input image',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--channel'],
            help = 'Channel to extract',
            type = int,
            default = 0,
        ),
    ]
    outputs = [
        dict(
            names = ['--out'],
            help = 'Output image',
            type = Path,
        ),
    ]
    
    def __init__(self, name):
        super(ExtractChannel, self).__init__(name)
    
    # def compute(self, *args, **kwargs):
    #     if not self.dirty: return
    #     data: pandas.DataFrame = self.getDataFrame()
    #     if isinstance(data, pandas.DataFrame):
    #         data = data.copy()
    #     else:
    #         return
    #     data[self.name + '_out'] = [getOutputFilePath(self.__class__.tool.info.inputs[0], self.name, i) for i in range(len(data))]
    #     self.outArray.setData(data)
    #     self.outArray.setClean()
    #     self.dirty = False

    def execute(self):
        data: pandas.DataFrame|None = self.getDataFrame()
        outputData: pandas.DataFrame = self.outArray.currentData()
        for index, row in data.iterrows():
            inputImage = sitk.ReadImage(self.getParameter('image', row))
            if 'vector' in inputImage.GetPixelIDTypeAsString():
                nChannels = inputImage.ToScalarImage().GetSize()[0]-1
                inputImage = inputImage[min(int(self.getParameter('channel', row)), nChannels), :, :]
            outputPath = Path(outputData.at[index, self.getFirstOuptutColumName()])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            sitk.WriteImage(inputImage, outputPath)
        self.finishExecution()
        return
    
class SubtractImages(SimpleITKBase):

    name = "subtract_images"
    description = "Subtract images."
    inputs = [
            dict(
            names = ['--image1'],
            help = 'Input image 1',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--image2'],
            help = 'Input image 2',
            type = Path,
            required = True,
            autoColumn = True,
        ),
    ]
    outputs = [
        dict(
            names = ['--out'],
            help = 'Output image',
            type = Path,
        ),
    ]

    def __init__(self, name):
        super(SubtractImages, self).__init__(name)
    
    # def compute(self, *args, **kwargs):
    #     if not self.dirty: return
    #     data: pandas.DataFrame = self.getDataFrame()
    #     if isinstance(data, pandas.DataFrame):
    #         data = data.copy()
    #     else:
    #         return
    #     data[self.name + '_out'] = [getOutputFilePath(self.__class__.tool.info.inputs[0], self.name, i) for i in range(len(data))]
    #     self.outArray.setData(data)
    #     self.outArray.setClean()
    #     self.dirty = False

    def execute(self):
        data: pandas.DataFrame = self.getDataFrame()
        outputData: pandas.DataFrame = self.outArray.currentData()
        for index, row in data.iterrows():
            inputImage1 = sitk.ReadImage(self.getParameter('image1', row), sitk.sitkInt32)
            inputImage2 = sitk.ReadImage(self.getParameter('image2', row), sitk.sitkInt32)
            resultImage = sitk.Subtract(inputImage1, inputImage2)
            outputPath = Path(outputData.at[index, self.getFirstOuptutColumName()])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            sitk.WriteImage(sitk.Cast(resultImage, sitk.sitkUInt8), outputPath)
        self.finishExecution()
        return
    
class ConnectedComponents(SimpleITKBase):

    name = "connected_components"
    description = "Compute connected components in the given binary image."
    inputs = [
            dict(
            names = ['--image'],
            help = 'Input image path',
            type = Path,
            required = True,
            autoColumn = True,
        ),
    ]
    outputs = [
        dict(
            names = ['--labeled_image'],
            help = 'Output image',
            type = Path,
        ),
        dict(
            names = ['--labeled_image_rgb'],
            help = 'Output rgb image',
            type = Path,
        ),
    ]

    def __init__(self, name):
        super(ConnectedComponents, self).__init__(name)

    # def compute(self, *args, **kwargs):
    #     if not self.dirty: return
    #     data: pandas.DataFrame = self.getDataFrame()
    #     if isinstance(data, pandas.DataFrame):
    #         data = data.copy()
    #     else:
    #         return
    #     li = [getOutputFilePath(self.__class__.tool.info.outputs[0], self.name, i) for i in range(len(data))]
    #     li = [outputPath.parent / f'{outputPath.stem}.nii' for outputPath in li]
    #     data[self.name + '_labeled_image'] = li
    #     data[self.name + '_labeled_image_rgb'] = [getOutputFilePath(self.__class__.tool.info.outputs[1], self.name, i) for i in range(len(data))]
    #     self.outArray.setData(data)
    #     self.outArray.setClean()
    #     self.dirty = False

    def execute(self):
        data: pandas.DataFrame = self.getDataFrame()
        outputData: pandas.DataFrame = self.outArray.currentData()
        for index, row in data.iterrows():
            inputImage = sitk.ReadImage(self.getParameter('image', row))
            labeledImage = sitk.ConnectedComponent(inputImage)
            outputPath = Path(outputData.at[index, self.getColumnName('labeled_image')])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            sitk.WriteImage(sitk.Cast(labeledImage, sitk.sitkUInt16), outputPath)
            # sitk.WriteImage(labeledImage, outputPath)
            outputPath = Path(outputData.at[index, self.getColumnName('labeled_image_rgb')])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            labeledImageRGB = sitk.LabelToRGB(labeledImage)
            sitk.WriteImage(labeledImageRGB, outputPath)
        self.finishExecution()
        return 
        
class LabelStatistics(SimpleITKBase):
    
    name = "label_statistics"
    description = "Compute label statistics from a label image."
    inputs = [
            dict(
            names = ['--image'],
            help = 'Input image',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--label'],
            help = 'Input label',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--minSize'],
            help = 'Min size of the labels',
            type = int,
            default = 100,
        ),
        dict(
            names = ['--maxSize'],
            help = 'Max size of the labels',
            type = int,
            default = 600,
        ),
    ]
    outputs = [
        dict(
            names = ['--connected_component'],
            help = 'Output connected component',
            type = Path,
        ),
    ]

    def __init__(self, name):
        super(LabelStatistics, self).__init__(name)

    # def compute(self, *args, **kwargs):
    #     if not self.dirty: return
    #     # data: pandas.DataFrame = self.getDataFrame()
    #     # if isinstance(data, pandas.DataFrame):
    #     #     data = data.copy()
    #     # else:
    #     #     return
    #     # data[self.name + 'connected_component'] = [getOutputFilePath(self.__class__.tool.info.outputs[0], self.name, i) for i in range(len(data))]
    #     # self.outArray.setData(data)
    #     # self.outArray.setClean()
    #     # self.dirty = False

    def compute(self, *args, **kwargs):
        self.outputMessage = 'Label statistics will be computed on execution.'
        return

    def execute(self):
        self.outputMessage = None
        data: pandas.DataFrame = self.getDataFrame()
        # outputData: pandas.DataFrame = self.outArray.currentData()
        records = []
        for index, row in data.iterrows():
            imagePath = self.getParameter('image', row)
            labelPath = self.getParameter('label', row)
            image = sitk.ReadImage(imagePath)
            if 'vector' in image.GetPixelIDTypeAsString():
                image = image.ToScalarImage()[0, :, :]
            label = sitk.ReadImage(labelPath)
            lsif = sitk.LabelStatisticsImageFilter()
            lsif.Execute(image, label)
            nLabels = lsif.GetNumberOfLabels()
            minSize = int(self.getParameter('minSize', row))
            maxSize = int(self.getParameter('maxSize', row))
            # for i in range(1, min(nLabels, maxNLabels)):
            for i in range(1, nLabels):
                minimum = lsif.GetMinimum(i)
                maximum = lsif.GetMaximum(i)
                median = lsif.GetMedian(i)
                mean = lsif.GetMean(i)
                numPixels = lsif.GetCount(i)
                bb = lsif.GetBoundingBox(i)
                if bb[0] == bb[1] or bb[2] == bb[3]: continue
                if numPixels < minSize or numPixels > maxSize: continue
                cc = image[bb[0]:bb[1], bb[2]:bb[3]]
                # dataImage = sitk.GetArrayFromImage(label)
                # cc = dataImage[bb[2]:bb[3], bb[0]:bb[1]]
                # cc = sitk.GetImageFromArray(cc)
                # cc = image[bb[0]:bb[1], bb[2]:bb[3]]
                # cc = image[bb[0]:bb[0]+bb[2]+1, bb[1]:bb[1]+bb[3]+1]
                # cc = image[bb[1]:bb[1]+bb[3], bb[0]:bb[0]+bb[2]]
                outputPath = self.getOutputDataFolderPath() / f'connected_component_{index}.png'
                outputPath.parent.mkdir(exist_ok=True, parents=True)
                sitk.WriteImage(cc, outputPath)
                records.append(dict(image=imagePath, label=labelPath, connected_component=outputPath, label_index=i, minimum=minimum, maximum=maximum, median=median, mean=mean, numPixels=numPixels, bb=str(bb)))
        outDataFrame = pandas.DataFrame.from_records(records)
        
        inmain(lambda: ThumbnailGenerator.get().generateThumbnails(self.name, outDataFrame))
        inmain(lambda: self.setOutputAndClean(outDataFrame))
        
        self.finishExecution()
        return 


def createSimpleITKNode(name, sitkFunction, tool):
    return type(name, (SimpleITKBase,), dict(sitkFunction=sitkFunction, tool=tool))

# import inspect
# import re

# members = inspect.getmembers(sitk)
# sitkFunctions = [m for m in members if len(m) >= 1 and inspect.isfunction(m[1]) ]

# for name, sitkFunction in sitkFunctions:
#     signature = inspect.signature(sitkFunction)
#     doc = inspect.getdoc(sitkFunction)
#     if "'" in doc or '"' in doc:
#         print(f'Warning: there is a string in the parameters of {name}, ignoring.')
#         continue
#     match = re.search(r'\((.*?)\)', doc)
#     if not match: continue
#     arguments = match.group(1).split(', ')
#     arguments = [a.split(' ') for a in arguments]
#     arguments = [dict() for a in arguments]

#     # inputs = [dict(name=name, description='', type=parameter.) for name, parameter in signature.parameters]


#     tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: name, inputs=[
#             dict(name='image1', description='Input image path', type='path'),
#             dict(name='channel', description='Channel to threshold', default_value=0, type='integer'),
#             dict(name='lowerThreshold', description='Lower threshold', default_value=0, type='integer'),
#             dict(name='upperThreshold', description='Upper threshold', default_value=255, type='integer'),
#             dict(name='insideValue', description='Inside value', default_value=1, type='integer'),
#             dict(name='outsideValue', description='Outside value', default_value=0, type='integer'),
#         ], outputs=[
#             dict(name='thresholded_image', description='Output image path', type='path'),
#         ])))

classes = {}

classes['BinaryThreshold'] = BinaryThreshold
classes['AddScalarToImage'] = AddScalarToImage
classes['ExtractChannel'] = ExtractChannel
classes['SubtractImages'] = SubtractImages
classes['ConnectedComponents'] = ConnectedComponents
classes['LabelStatistics'] = LabelStatistics

def createFunctionNodes():

    with open(getSourcesPath() / 'Scripts' / 'simpleITK_functions.json', 'r') as f:
        tools = json.load(f)

    for tool in tools.values():
        name = tool['name']
        functionName = tool['function_name']
        if name in classes: continue
        tool = DefaultMunch.fromDict(dict(info=dict(fullname=(lambda name=name: name), inputs=tool['inputs'], outputs=tool['outputs'], help=tool['description'], categories='SimpleITK|All')))
        if hasattr(sitk, functionName):
            classes[name] = createSimpleITKNode(name, getattr(sitk, functionName), tool)
        else:
            print(f'Warning: sitk has no {functionName} function.')

    return classes
