from pathlib import Path
import uuid
from PyFlow import INITIALIZE, GET_PACKAGES
from PyFlow.Core.Common import connectPins
from PyFlow.Core.GraphManager import GraphManagerSingleton
from PyFlow.Core.NodeBase import NodeBase
from PyFlow.ThumbnailManagement.ThumbnailGenerator import ThumbnailGenerator

class WorkflowManager:
    def __init__(self, workflowPath:Path):
            
        INITIALIZE()
        self.graphManager = GraphManagerSingleton().get()
        workflowPath.mkdir(exist_ok=True, parents=True)
        self.graphManager.workflowPath = workflowPath
        ThumbnailGenerator.get().setWorkflowPathAndLoadImageToThumbnail(workflowPath)

        package = GET_PACKAGES()['PyFlowBase']
        self.nodeClasses = package.GetNodeClasses()

        self.graphManager.activeGraph().populating = True
    
    def initializeNode(self, nodeClassName):
        id = str(uuid.uuid4())
        node = self.nodeClasses[nodeClassName](nodeClassName)

        nodeTemplate = NodeBase.jsonTemplate()
        nodeTemplate["package"] = 'PyFlowBase'
        nodeTemplate["lib"] = 'BiitLib'
        nodeTemplate["type"] = node.__class__.name
        nodeTemplate["name"] = node.name
        nodeTemplate["meta"]["label"] = node.__class__.name
        nodeTemplate["uuid"] = id
        nodeTemplate["x"] = 0
        nodeTemplate["y"] = 0
        
        self.graphManager.activeGraph().addNode(node, nodeTemplate)
        return node

    def connect(self, nodeA, nodeB):
        connectPins(nodeA.outArray, nodeB.inArray)

    def setupConnections(self):
        nodes = self.graphManager.getAllNodes()
        
        for node in nodes:
            node.setupConnections()
    
    def computeNodes(self, nodes=None):
        nodes = nodes or self.graphManager.getAllNodes()
        for node in nodes:
            node.dirty = True
            node.compute()
        
    def isBiitLib(self, node):
        return node.lib == 'BiitLib'

    def wasExecuted(self, node):
        return hasattr(node, 'executed') and node.executed

    def isPlanned(self, node):
        return hasattr(node, 'planned') and node.planned

    def mustExecute(self, node):
        return self.isBiitLib(node) and not self.wasExecuted(node)

    def getNodesToExecute(self, nodes):
        return [ node for node in nodes if self.mustExecute(node) ]

    def getInputNodes(self, node):
        return [outputPin.owningNode() for inputPin in node.inputs.values() for outputPin in inputPin.affected_by]

    def inputsWereExecuted(self, node):
        return len(node.inputs) == 0 or all([not self.isBiitLib(n) or self.wasExecuted(n) for n in self.getInputNodes(node)])

    def inputsArePlannedOrExecuted(self, node):
        return len(node.inputs) == 0 or all([not self.isBiitLib(n) or (self.isPlanned(n) or self.wasExecuted(n)) for n in self.getInputNodes(node)])

    def planExecution(self, node):
        if not self.inputsArePlannedOrExecuted(node): return False
        node.planned = True
        return True

    def executeNode(self, node):
        if not self.inputsWereExecuted(node): return False
        node.execute()
        return True

    def executeWorkflow(self):

        # workflow()

        nodes = self.graphManager.getAllNodes()
        
        nodesToExecute = set(self.getNodesToExecute(nodes))

        for node in nodesToExecute:
            node.planned = False
        
        plannedNodes = []
        while len(nodesToExecute)>0:
            lastN = len(nodesToExecute)
            for node in nodesToExecute.copy():
                if self.planExecution(node):
                    plannedNodes.append(node)
                    nodesToExecute.remove(node)
            if len(nodesToExecute) == lastN:
                raise Exception('Error: there is a cycle in the graph, some nodes cannot be executed.')

        for n, node in enumerate(plannedNodes):
            print(f'Process node [[{n}/{len(plannedNodes)}]]: {node.name}')
            self.executeNode(node)

        print('All node processed')
