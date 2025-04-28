# BioImageIT programmatic API

BioImageIT allows you to create and execute workflows in pure Python.

Here is an example usage:

```
from pathlib import Path
from PyFlow.WorkflowManager import WorkflowManager

# Initialize the workflow manager with the path of your workflow
workflowManager = WorkflowManager(Path('/Users/amasson/BioImageIT/DemoWorkflow'))

# Create nodes

listFiles = workflowManager.initializeNode('ListFiles')

binaryThreshold = workflowManager.initializeNode('binary_threshold')
connectedComponents = workflowManager.initializeNode('connected_components')
labelStatistics = workflowManager.initializeNode('label_statistics')

extractChannel0 = workflowManager.initializeNode('extract_channel')
extractChannel1 = workflowManager.initializeNode('extract_channel')

concatDataFrames = workflowManager.initializeNode('Concat')

subtractImages = workflowManager.initializeNode('subtract_images')

atlas = workflowManager.initializeNode('atlas')

# Setup connections

workflowManager.setupConnections()

workflowManager.connect(listFiles, binaryThreshold)
workflowManager.connect(binaryThreshold, connectedComponents)
workflowManager.connect(connectedComponents, labelStatistics)

workflowManager.connect(listFiles, extractChannel0)
workflowManager.connect(listFiles, extractChannel1)

workflowManager.connect(extractChannel0, concatDataFrames)
workflowManager.connect(extractChannel1, concatDataFrames)

workflowManager.connect(concatDataFrames, subtractImages)
workflowManager.connect(subtractImages, atlas)

# Set node parameters

listFiles.parameters['inputs']['folderPath']['value'] = '/Users/amasson/Documents/DemoData/CellPose/CellPoseExamples'
listFiles.parameters['inputs']['columnName']['value'] = 'CellPoseExamples'
binaryThreshold.parameters['inputs']['channel']['value'] = 0
binaryThreshold.parameters['inputs']['lowerThreshold']['value'] = 0
binaryThreshold.parameters['inputs']['upperThreshold']['value'] = 130
binaryThreshold.parameters['inputs']['insideValue']['value'] = 255
binaryThreshold.parameters['inputs']['outsideValue']['value'] = 0
labelStatistics.parameters['inputs']['minSize']['value'] = 350
labelStatistics.parameters['inputs']['maxSize']['value'] = 500
extractChannel0.parameters['inputs']['channel']['value'] = 0
extractChannel1.parameters['inputs']['channel']['value'] = 1

# Execute the workflow

workflowManager.computeNodes()
workflowManager.executeWorkflow()
```