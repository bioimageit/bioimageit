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
import shutil

from qtpy import QtCore, QtWidgets
from PyFlow.Packages.PyFlowBase.Factories.PinInputWidgetFactory import PathInputWidget
from PyFlow.ConfigManager import ConfigManager
from PyFlow.UI.Tool.Tool import DockTool
from PyFlow.UI.Widgets.FileDialog import FileDialog

from PyFlow.Packages.PyFlowBase.Tools.RunTool import RunTool, RunAllTool, RunSelectedTool, ExportWorkflowTool
from PyFlow.Packages.PyFlowBase.Tools.ClearTool import ClearTool, ClearAllTool, ClearSelectedTool
from PyFlow.UI.Widgets.PropertiesFramework import CollapsibleWidget

class ExecutionTool(DockTool):
    """docstring for Execution tool."""

    def __init__(self):
        super(ExecutionTool, self).__init__()
        self.content = None

        # self.scrollArea = QtWidgets.QScrollArea(self)
        # self.scrollArea.setWidgetResizable(True)

        self.mainWidget = QtWidgets.QWidget()
        
        self.mainLayout = QtWidgets.QVBoxLayout()

        self.runTool = RunTool()
        self.runSelectedTool = RunSelectedTool()
        self.clearSelectedTool = ClearSelectedTool()

        # iconSize = QtCore.QSize(self._iconSize, self._iconSize)
        self.executeLayout = QtWidgets.QVBoxLayout()
        self.runButton = QtWidgets.QPushButton("Run unexecuted nodes")
        self.runButton.setIcon(RunTool.getIcon())
        # self.runButton.setIconSize(iconSize)
        self.runButton.clicked.connect(self.runTool.do)
        self.executeLayout.addWidget(self.runButton)
        self.runSelectedButton = QtWidgets.QPushButton("Run selected nodes")
        self.runSelectedButton.setIcon(RunSelectedTool.getIcon())
        # self.runSelectedButton.setIconSize(iconSize)
        self.runSelectedButton.clicked.connect(self.runSelectedTool.do)
        self.executeLayout.addWidget(self.runSelectedButton)
        self.clearSelectedButton = QtWidgets.QPushButton("Clear selected nodes")
        self.clearSelectedButton.setIcon(ClearSelectedTool.getIcon())
        # self.clearSelectedButton.setIconSize(iconSize)
        self.clearSelectedButton.clicked.connect(self.clearSelectedTool.do)
        self.executeLayout.addWidget(self.clearSelectedButton)

        self.mainLayout.addLayout(self.executeLayout)
        self.mainLayout.addStretch()

        self.mainWidget.setLayout(self.mainLayout)
        
        # self.scrollArea.setWidget(self.mainWidget)

        self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        # self.scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)

        self.setWidget(self.mainWidget)
    
    @staticmethod
    def isMovable():
        return False
    
    @staticmethod
    def isClosable():
        return False
    
    @staticmethod
    def getDefaultWorkflowPath():
        return Path.home() / 'BioImageIT' / 'Workflow1'

    def setAppInstance(self, pyFlowInstance):
        super().setAppInstance(pyFlowInstance)
        self.runTool.pyFlowInstance = pyFlowInstance
        self.runSelectedTool.pyFlowInstance = pyFlowInstance
        self.clearSelectedTool.pyFlowInstance = pyFlowInstance
    
    def onShow(self):
        super().onShow()
        self.setMinimumSize(QtCore.QSize(200, 50))
    
    @staticmethod
    def isSingleton():
        return True

    @staticmethod
    def defaultDockArea():
        return QtCore.Qt.LeftDockWidgetArea

    @staticmethod
    def defaultSubDockArea():
        return "Tab:Tools"
    
    @staticmethod
    def toolTip():
        return "Execution"

    @staticmethod
    def name():
        return "Execution"
