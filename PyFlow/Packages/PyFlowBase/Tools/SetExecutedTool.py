## Copyright 2015-2019 Ilgar Lunin, Pedro Cabrera

## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at

##     http://www.apache.org/licenses/LICENSE-2.0

## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

from qtpy import QtGui
from qtpy.QtWidgets import *

from PyFlow.UI.Tool.Tool import ShelfTool
from PyFlow.UI.Widgets import BlueprintCanvas
from PyFlow.Packages.PyFlowBase.Tools import RESOURCES_DIR
from PyFlow.Packages.PyFlowBase.Tools.RunTool import RunTool

class SetSelectedExecutedTool(ShelfTool):
    """docstring for SetSelectedExecutedTool."""

    def __init__(self):
        super(SetSelectedExecutedTool, self).__init__()

    @staticmethod
    def toolTip():
        return "Set selected nodes executed"
    
    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "biit/check.png")
    
    @staticmethod
    def name():
        return "Set selected executed"
    
    def getNodesToSet(self, nodes):
        canvas: BlueprintCanvas = self.pyFlowInstance.getCanvas()
        selectedNodeNames = [node.name for node in canvas.selectedNodes()]
        return [ node for node in nodes if RunTool.isBiitLib(node) and node.name in selectedNodeNames]
    
    def do(self):

        graphManager = self.pyFlowInstance.graphManager.get()
        nodes = graphManager.getAllNodes()
        nodesToSet = self.getNodesToSet(nodes)
        for node in nodesToSet:
            node.setExecuted(True)
