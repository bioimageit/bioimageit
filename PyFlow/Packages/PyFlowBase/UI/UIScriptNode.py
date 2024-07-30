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

import subprocess
from pathlib import Path
from qtpy.QtWidgets import QFileDialog, QPushButton
from PyFlow.UI.Canvas.UINodeBase import UINodeBase
from PyFlow.Core.Common import *
from PyFlow.UI.Widgets.InputWidgets import createInputWidget
from PyFlow.ConfigManager import ConfigManager
from PyFlow import getRootPath
from PyFlow.Core.GraphManager import GraphManagerSingleton

class UIScriptNode(UINodeBase):
    def __init__(self, raw_node):
        super(UIScriptNode, self).__init__(raw_node)

    def createScript(self):
        app = self.canvasRef().pyFlowInstance
        graphManager = GraphManagerSingleton().get()
        scriptPath, _ = QFileDialog.getSaveFileName(app, "Create script", str(Path(graphManager.workflowPath / 'Scripts').resolve()), "All Files(*);;Python Files(*.py)", options = QFileDialog.HideNameFilterDetails)
        scriptPath.parent.mkdir(exist_ok=True, parents=True)
        self._rawNode.scriptPath = scriptPath
        examplePath = getRootPath() / 'PyFlow' / 'Scripts' / 'template.py'
        with open(scriptPath, 'w') as destinationFile, open(examplePath, 'r') as exampleFile:
            destinationFile.write(exampleFile.read())
        editCmd = ConfigManager().getPrefsValue("PREFS", "General/EditorCmd")
        editCmd = editCmd.replace("@FILE", scriptPath)
        subprocess.Popen(editCmd, shell=True)
        if self.openScriptWidget:
            self.openScriptWidget.setWidgetValue(scriptPath)
    
    def createInputWidgets(self, inputsCategory, inGroup=None, pins=True):
        # createScriptButton = createInputWidget('ExecPin', lambda: self.createFile(), 'Create script')
        # if createScriptButton:
        #     createScriptButton.setToolTip('Create script')
        #     createScriptButton.setObjectName('CreateScript')
        #     inputsCategory.addWidget('Create Script', createScriptButton, group=inGroup)
        self.createScriptButton = QPushButton('Create script')
        self.createScriptButton.clicked.connect(self.createScript)
        inputsCategory.Layout.addWidget(self.createScriptButton)

        self.openScriptWidget = createInputWidget('StringPin', lambda value: self._rawNode.scriptPathChanged(value), '', 'FilePathWidget')
        if self.openScriptWidget:
            self.openScriptWidget.setToolTip('Script path')
            self.openScriptWidget.blockWidgetSignals(True)
            self.openScriptWidget.setWidgetValue(self._rawNode.scriptPath if self._rawNode.scriptPath is not None else '')
            self.openScriptWidget.blockWidgetSignals(False)
            self.openScriptWidget.setObjectName('ScriptPath')
            inputsCategory.addWidget('Script path', self.openScriptWidget, group=inGroup)
        self.executeButton = QPushButton('Execute')
        self.executeButton.clicked.connect(lambda: self._rawNode.executeScript())
        inputsCategory.Layout.addWidget(self.executeButton)
    
    # def createFile(self):
    #     fileName = QFileDialog.getSaveFileName(self, "Create python script", str(Path.home()), "Python script (*.py)")
    #     self.openScriptWidget.setWidgetValue(fileName)
    #     # self._rawNode.scriptPathChanged(fileName)