from pathlib import Path
import uuid
from PyFlow import INITIALIZE
from PyFlow.Packages.PyFlowBase.FunctionLibraries.PandasLib import ListFiles, ConcatDataFrames
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitSimpleITKNodes import BinaryThreshold, ConnectedComponents, LabelStatistics, ExtractChannel, SubtractImages
from PyFlow.Core.Common import connectPins
from PyFlow.Core.GraphManager import GraphManagerSingleton
from PyFlow.Core.NodeBase import NodeBase
from PyFlow.ThumbnailManagement.ThumbnailGenerator import ThumbnailGenerator

INITIALIZE()
graphManager = GraphManagerSingleton().get()
workflowPath = Path('Workflows/DemoWorkflow/')
workflowPath.mkdir(exist_ok=True, parents=True)
graphManager.workflowPath = workflowPath
ThumbnailGenerator.get().setWorkflowPathAndLoadImageToThumbnail(workflowPath)

def initializeNode(node):
    # jsonTemplate = node.serialize()
    # jsonTemplate["wrapper"] = node.wrapperJsonData

    nodeTemplate = NodeBase.jsonTemplate()
    nodeTemplate["package"] = 'PyFlowBase'
    nodeTemplate["lib"] = 'BiitLib'
    nodeTemplate["type"] = node.__class__.name
    nodeTemplate["name"] = node.name
    nodeTemplate["meta"]["label"] = node.__class__.name
    nodeTemplate["uuid"] = str(uuid.uuid4())
    nodeTemplate["x"] = 0
    nodeTemplate["y"] = 0
    
    graphManager.activeGraph().addNode(node, nodeTemplate)

def connect(nodeA, nodeB):
    connectPins(nodeA.outArray, nodeB.inArray)

def workflow():
    listFiles = ListFiles('List files')
    initializeNode(listFiles)

    listFiles.pathPin.setData(Path('/Users/amasson/Documents/DemoData/CellPose/CellPoseExamples'))
    listFiles.columnNamePin.setData('CellPoseExamples')

    binaryThreshold = BinaryThreshold('Binary threshold')
    initializeNode(binaryThreshold)

    connectedComponents = ConnectedComponents('Connected components')
    initializeNode(connectedComponents)
    labelStatistics = LabelStatistics('Label statistics')
    initializeNode(labelStatistics)

    extractChannel0 = ExtractChannel('Extract channel 0')
    extractChannel1 = ExtractChannel('Extract channel 1')
    initializeNode(extractChannel0)
    initializeNode(extractChannel1)

    concatDataFrames = ConcatDataFrames('Concat DataFrames')
    initializeNode(concatDataFrames)

    subtractImages = SubtractImages('Subtract Images')
    initializeNode(subtractImages)

    nodes = graphManager.getAllNodes()
    
    for node in nodes:
        node.setupConnections()

    connect(listFiles, binaryThreshold)
    connect(binaryThreshold, connectedComponents)
    connect(connectedComponents, labelStatistics)

    connect(listFiles, extractChannel0)
    connect(listFiles, extractChannel1)
    
    connect(extractChannel0, concatDataFrames)
    connect(extractChannel1, concatDataFrames)
    
    connect(concatDataFrames, subtractImages)

    for node in nodes:
        node.dirty = True
        node.compute()
    
    binaryThreshold.parameters['inputs']['channel']['value'] = 0
    binaryThreshold.parameters['inputs']['lowerThreshold']['value'] = 0
    binaryThreshold.parameters['inputs']['upperThreshold']['value'] = 130
    binaryThreshold.parameters['inputs']['insideValue']['value'] = 255
    binaryThreshold.parameters['inputs']['outsideValue']['value'] = 0
    labelStatistics.parameters['inputs']['minSize']['value'] = 350
    labelStatistics.parameters['inputs']['maxSize']['value'] = 500
    extractChannel0.parameters['inputs']['channel']['value'] = 0
    extractChannel1.parameters['inputs']['channel']['value'] = 1

def isBiitLib(node):
    return node.lib == 'BiitLib'

def wasExecuted(node):
    return hasattr(node, 'executed') and node.executed

def isPlanned(node):
    return hasattr(node, 'planned') and node.planned

def mustExecute(node):
    return isBiitLib(node) and not wasExecuted(node)

def getNodesToExecute(nodes):
    return [ node for node in nodes if mustExecute(node) ]

def getInputNodes(node):
    return [outputPin.owningNode() for inputPin in node.inputs.values() for outputPin in inputPin.affected_by]

def inputsWereExecuted(node):
    return len(node.inputs) == 0 or all([not isBiitLib(n) or wasExecuted(n) for n in getInputNodes(node)])

def inputsArePlannedOrExecuted(node):
    return len(node.inputs) == 0 or all([not isBiitLib(n) or (isPlanned(n) or wasExecuted(n)) for n in getInputNodes(node)])

def planExecution(node):
    if not inputsArePlannedOrExecuted(node): return False
    node.planned = True
    return True

def executeNode(node):
    if not inputsWereExecuted(node): return False
    node.execute()
    return True

def executeWorkflow():

    graphManager.activeGraph().populating = True
    workflow()

    nodes = graphManager.getAllNodes()
    
    nodesToExecute = set(getNodesToExecute(nodes))

    for node in nodesToExecute:
        node.planned = False
    
    plannedNodes = []
    while len(nodesToExecute)>0:
        lastN = len(nodesToExecute)
        for node in nodesToExecute.copy():
            if planExecution(node):
                plannedNodes.append(node)
                nodesToExecute.remove(node)
        if len(nodesToExecute) == lastN:
            raise Exception('Error: there is a cycle in the graph, some nodes cannot be executed.')

    for n, node in enumerate(plannedNodes):
        print(f'Process node [[{n}/{len(plannedNodes)}]]: {node.name}')
        executeNode(node)

    print('All node processed')

executeWorkflow()