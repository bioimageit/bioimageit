from pathlib import Path
import pandas

from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitUtils import getOutputFilePath
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase
from PyFlow.invoke_in_main import inmain
from PyFlow.Packages.PyFlowBase.Tools.ThumbnailGenerator import thumbnailGenerator

from munch import DefaultMunch
# import re
import SimpleITK as sitk

class SimpleITKBase(BiitArrayNodeBase):

    def __init__(self, name):
        super(SimpleITKBase, self).__init__(name)

    @staticmethod
    def category():
        return "SimpleITK"
    
    def getParameter(self, name, row):
        return self.parameters[name]['value'] if self.parameters[name]['type'] == 'value' else row[self.parameters[name]['columnName']]
    
class BinaryThreshold(SimpleITKBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'binary_threshold', inputs=[
            dict(name='image1', description='Input image path', type='imagepng'),
            dict(name='channel', description='Channel to threshold', default_value=0, type='integer'),
            dict(name='lowerThreshold', description='Lower threshold', default_value=0, type='integer'),
            dict(name='upperThreshold', description='Upper threshold', default_value=255, type='integer'),
            dict(name='insideValue', description='Inside value', default_value=1, type='integer'),
            dict(name='outsideValue', description='Outside value', default_value=0, type='integer'),
        ], outputs=[
            dict(name='thresholded_image', description='Output image path', type='imagepng'),
        ])))
    
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
        data: pandas.DataFrame = self.getDataFrame()
        if data is None:
            self.executed = True 
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
            outputPath = Path(outputData.at[index, self.name + '_thresholded_image'])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            sitk.WriteImage(thresholdedImage, outputPath)
        self.executed = True
        return 
    
class AddScalarToImage(SimpleITKBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'add_scalar_to_images', inputs=[
            dict(name='image', description='Input image', type='imagepng'),
            dict(name='value', description='Value to add', default_value=50, type='integer')
        ], outputs=[
            dict(name='out', description='Output image', type='imagetiff'),
        ])))
    
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
    #     self.executed = True
    #     return
    
class ExtractChannel(SimpleITKBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'extract_channel', inputs=[
            dict(name='image', description='Input image', type='imagepng'),
            dict(name='channel', description='Channel to extract', default_value=0, type='integer'),
        ], outputs=[
            dict(name='out', description='Output image', type='imagetiff'),
        ])))
    
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
        data: pandas.DataFrame = self.getDataFrame()
        outputData: pandas.DataFrame = self.outArray.currentData()
        for index, row in data.iterrows():
            inputImage = sitk.ReadImage(self.getParameter('image', row))
            if 'vector' in inputImage.GetPixelIDTypeAsString():
                nChannels = inputImage.ToScalarImage().GetSize()[0]-1
                inputImage = inputImage[min(int(self.getParameter('channel', row)), nChannels), :, :]
            outputPath = Path(outputData.at[index, self.name + '_out'])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            sitk.WriteImage(inputImage, outputPath)
        self.executed = True
        return
    
class SubtractImages(SimpleITKBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'subtract_images', inputs=[
            dict(name='image1', description='Input image 1', type='imagepng'),
            dict(name='image2', description='Input image 2', type='imagepng'),
        ], outputs=[
            dict(name='out', description='Output image', type='imagetiff'),
        ])))
    
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
            outputPath = Path(outputData.at[index, self.name + '_out'])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            sitk.WriteImage(sitk.Cast(resultImage, sitk.sitkUInt8), outputPath)
        self.executed = True
        return
    
class ConnectedComponents(SimpleITKBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'connected_components', inputs=[
            dict(name='image', description='Input image path', type='imagepng'),
        ], outputs=[
            dict(name='labeled_image', description='Output image', type='imagetiff'),
            dict(name='labeled_image_rgb', description='Output rgb image', type='imagepng'),
        ])))
    
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
            outputPath = Path(outputData.at[index, self.name + '_labeled_image'])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            sitk.WriteImage(sitk.Cast(labeledImage, sitk.sitkUInt16), outputPath)
            # sitk.WriteImage(labeledImage, outputPath)
            outputPath = Path(outputData.at[index, self.name + '_labeled_image_rgb'])
            outputPath.parent.mkdir(exist_ok=True, parents=True)
            labeledImageRGB = sitk.LabelToRGB(labeledImage)
            sitk.WriteImage(labeledImageRGB, outputPath)
        self.executed = True
        return 
        
class LabelStatistics(SimpleITKBase):

    tool = DefaultMunch.fromDict(dict(info=dict(fullname=lambda: 'connected_components', inputs=[
            dict(name='image', description='Input image', type='imagepng'),
            dict(name='label', description='Input label', type='imagepng'),
            dict(name='minSize', description='Min size of the labels', default_value=100, type='integer'),
            dict(name='maxSize', description='Max size of the labels', default_value=600, type='integer'),
        ], outputs=[
            dict(name='connected_component', description='Output connected component', type='imagepng')
        ])))
    
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
        n = 0
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
                outputPath = getOutputFilePath(self.__class__.tool.info.outputs[0], self.name, n)
                n += 1
                outputPath.parent.mkdir(exist_ok=True, parents=True)
                sitk.WriteImage(cc, outputPath)
                records.append(dict(image=imagePath, label=labelPath, connected_component=outputPath, label_index=i, minimum=minimum, maximum=maximum, median=median, mean=mean, numPixels=numPixels, bb=str(bb)))
        outDataFrame = pandas.DataFrame.from_records(records)
        
        inmain(lambda: thumbnailGenerator.generateThumbnails(self.name, outDataFrame))
        inmain(lambda: self.setOutputAndClean(outDataFrame))
        
        self.executed = True
        return 
        