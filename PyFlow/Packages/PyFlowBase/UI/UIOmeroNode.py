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
from qtpy.QtWidgets import QComboBox
from PyFlow.UI.Canvas.UINodeBase import UINodeBase
from PyFlow.UI.Canvas.UICommon import NodeDefaults
from PyFlow.Core.Common import *

class UIOmeroNode(UINodeBase):
    def __init__(self, raw_node):
        super(UIOmeroNode, self).__init__(raw_node)
        raw_node.executedChanged.connect(self.executedChanged)
    
    def executedChanged(self, executed:bool):
        if executed:
            self.headColorOverride = NodeDefaults().PURE_NODE_HEAD_COLOR
            self.headColor = NodeDefaults().PURE_NODE_HEAD_COLOR
        else:
            self.headColorOverride = QtGui.QColor(100, 100, 100, 150)
            self.headColor = QtGui.QColor(100, 100, 100, 150)

class UIOmeroDownload(UINodeBase):
    def __init__(self, raw_node):
        super(UIOmeroDownload, self).__init__(raw_node)
        raw_node.datasetIdPin.dataBeenSet.connect(self.datasetChanged)
        raw_node.datasetNamePin.dataBeenSet.connect(self.datasetChanged)
    
    def datasetChanged(self, datasetName:str):
        self._rawNode.processNode(True)
        self.canvasRef().tryFillPropertiesView(self)
        self.canvasRef().tryFillTableView(self)

class UIOmeroUpload(UIOmeroNode):
    def __init__(self, raw_node):
        super(UIOmeroNode, self).__init__(raw_node)
    
    def changeColumn(self, index):
        self._rawNode.columnName = self.columnSelector.itemText(index)
    
    def createInputWidgets(self, inputsCategory, inGroup=None, pins=True):
        self._rawNode.inDataFrame.hidden = True
        
        data = self._rawNode.getDataFrame()
        if data is not None and len(data.columns)>0:
            self.columnSelector = QComboBox()
            for column in data.columns:
                self.columnSelector.addItem(column)
            self.columnSelector.activated.connect(self.changeColumn)
            columnIndex = list(data.columns).index(self._rawNode.columnName) if self._rawNode.columnName in data.columns else len(data.columns)-1
            self.columnSelector.setCurrentIndex(columnIndex)
            inputsCategory.addWidget('Column name', self.columnSelector, group=inGroup)
        
        super(UIOmeroUpload, self).createInputWidgets(inputsCategory, inGroup)

        self._rawNode.inDataFrame.hidden = False