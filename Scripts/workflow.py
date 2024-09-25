from pathlib import Path
from PyFlow.Packages.PyFlowBase.FunctionLibraries.PandasLib import ListFiles, ConcatDataFrames
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitSimpleITKNodes import BinaryThreshold, ConnectedComponents, LabelStatistics, ExtractChannel, SubtractImages
from PyFlow.Core.Common import connectPins
from PyFlow.Core import PinBase


listFiles = ListFiles('List files')
# pathPin:PinBase = listFiles.pathPin
listFiles.pathPin.setData(Path('/Users/amasson/Documents/DemoData/CellPose/CellPoseExamples'))
listFiles.columnNamePin.setData('CellPoseExamples')

binaryThreshold = BinaryThreshold('Binary threshold')
binaryThreshold.parameters['channel']['value'] = 0
binaryThreshold.parameters['lowerThreshold']['value'] = 0
binaryThreshold.parameters['upperThreshold']['value'] = 130
binaryThreshold.parameters['insideValue']['value'] = 255
binaryThreshold.parameters['outsideValue']['value'] = 0

connectedComponents = ConnectedComponents('Connected components')
labelStatistics = LabelStatistics('Label statistics')
labelStatistics.parameters['minSize']['value'] = 350
labelStatistics.parameters['maxSize']['value'] = 500

connectPins(listFiles.outArray, binaryThreshold.inArray)
connectPins(binaryThreshold.outArray, connectedComponents.inArray)
connectPins(connectedComponents.outArray, labelStatistics.inArray)

extractChannel0 = ExtractChannel('Extract channel 0')
extractChannel0.parameters['channel']['value'] = 0
extractChannel1 = ExtractChannel('Extract channel 1')
extractChannel1.parameters['channel']['value'] = 1

connectPins(listFiles.outArray, extractChannel0.inArray)
connectPins(listFiles.outArray, extractChannel1.inArray)

concatDataFrames = ConcatDataFrames('Concat DataFrames')

connectPins(extractChannel0.outArray, concatDataFrames.inArray)
connectPins(extractChannel1.outArray, concatDataFrames.inArray)

subtractImages = SubtractImages('Subtract Images')

connectPins(concatDataFrames.outArray, subtractImages.inArray)
