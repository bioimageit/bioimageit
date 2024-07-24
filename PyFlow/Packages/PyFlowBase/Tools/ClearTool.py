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

from pathlib import Path
import json

from qtpy import QtGui
from qtpy.QtWidgets import *

from PyFlow.UI.Tool.Tool import ShelfTool
from PyFlow.UI.Widgets import BlueprintCanvas
from PyFlow.Packages.PyFlowBase.Tools import RESOURCES_DIR
from PyFlow.Packages.PyFlowBase.Tools.RunTool import RunTool, RunAllTool, RunSelectedTool

class ClearTool(ShelfTool):
    """docstring for ClearTool."""

    def __init__(self):
        super(ClearTool, self).__init__()

    @staticmethod
    def toolTip():
        return "Clear changed nodes"

    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "biit/delete-bin-4-fill.svg")

    @staticmethod
    def name():
        return "Clear"
    
    def getNodesToClear(self, nodes):
        return [ node for node in nodes if RunTool.isBiitLib(node) and RunTool.wasExecuted(node) ]
    
    def do(self):

        graphManager = self.pyFlowInstance.graphManager.get()
        nodes = graphManager.getAllNodes()
        nodesToClear = self.getNodesToClear(nodes)
        for node in nodesToClear:
            node.clear()

class ClearAllTool(ClearTool):
    """docstring for ClearAllTool."""

    def __init__(self):
        super(ClearAllTool, self).__init__()

    @staticmethod
    def toolTip():
        return "Clear all nodes"
    
    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "biit/delete-bin-5-fill.svg")
    
    @staticmethod
    def name():
        return "Clear all"
    
    def do(self):
        graphManager = self.pyFlowInstance.graphManager.get()
        for node in graphManager.getAllNodes():
            if ClearTool.isBiitLib(node):
                node.setExecuted(False)
        super(ClearAllTool, self).do()

class ClearSelectedTool(ClearTool):
    """docstring for ClearSelectedTool."""

    def __init__(self):
        super(ClearSelectedTool, self).__init__()

    @staticmethod
    def toolTip():
        return "Clear selected nodes"
    
    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "biit/delete-bin-4-line.svg")
    
    @staticmethod
    def name():
        return "Clear selected"
    
    def getNodesToClear(self, nodes):
        canvas: BlueprintCanvas = self.pyFlowInstance.getCanvas()
        selectedNodeNames = [node.name for node in canvas.selectedNodes()]
        return [ node for node in nodes if RunTool.isBiitLib(node) and node.name in selectedNodeNames]