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

import pandas
from qtpy import QtGui, QtCore
from qtpy.QtWidgets import QWidget, QComboBox, QHBoxLayout, QFrame, QLabel
from PyFlow.UI.Canvas.UINodeBase import UINodeBase
from PyFlow.UI.Canvas.UICommon import NodeDefaults
from PyFlow.Core.Common import *
from PyFlow.UI.Widgets.InputWidgets import createInputWidget, InputWidgetRaw
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitUtils import getPinTypeFromIoType, filePathTypes

class ColumnValueWidget(QWidget):

    def __init__(self, input, node, parent=None):
        super(ColumnValueWidget, self).__init__(parent=parent)
        self.name = input.name
        self.inputWidget = self.createInput(input.name, input.type, input.description, input.default_value, input.select_info if hasattr(input, 'select_info') else None)
        self.node = node
        self.setContentsMargins(0, 0, 0, 0)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.typeSelector = QComboBox()
        self.typeSelector.addItem('Column')
        self.typeSelector.addItem('Value')
        self.layout.addWidget(self.typeSelector)
        self.layout.addWidget(self.inputWidget)
        type = node.parameters[input.name]['type']
        data = node.inArray.currentData()
        isDataframe = isinstance(data, pandas.DataFrame)
        node.inArray.setClean()
        defaultColumnName = node.parameters[input.name]['columnName'] if not isDataframe or node.parameters[input.name]['columnName'] in data.columns else data.columns[-1]
        node.parameters[input.name]['columnName'] = defaultColumnName
        # self.columnNameInput = createInputWidget('StringPin', lambda value: self.updateNodeParameters(value, 'columnName'), defaultColumnName, DEFAULT_WIDGET_VARIANT)
        # self.layout.addWidget(self.columnNameInput)
        self.typeSelector.activated.connect(self.changeTypeValue)
        # self.columnNameInput.blockWidgetSignals(True)
        # self.columnNameInput.setWidgetValue(defaultColumnName)
        # self.columnNameInput.blockWidgetSignals(False)
        if isinstance(self.inputWidget, InputWidgetRaw):
            self.inputWidget.blockWidgetSignals(True)
            self.inputWidget.setWidgetValue(node.parameters[input.name]['value'])
            self.inputWidget.blockWidgetSignals(False)
        self.columnSelector = None
        index = 0 if type == 'columnName' and isDataframe else 1
        if isDataframe:
            # self.columnNameInput.hide()
            self.columnSelector = QComboBox()
            for column in data.columns:
                self.columnSelector.addItem(column)
            self.columnSelector.setCurrentIndex(list(data.columns).index(defaultColumnName))
            self.columnSelector.activated.connect(self.changeColumnValue)
            self.layout.addWidget(self.columnSelector)
        else:
            self.typeSelector.hide()
        self.typeSelector.setCurrentIndex(index)
        self.changeTypeValue(index, False)
    
    # inputWidgetVariant: PathWidget, FilePathWidget, FolderPathWidget, ObjectPathWidth, EnumWidget
    def createInput(self, name, type, description, defaultValue, selectInfo):
        if type == 'select':
            w = QComboBox()
            for name in selectInfo.names:
                w.addItem(name)
            w.setCurrentIndex(selectInfo.values.index(defaultValue) if defaultValue in selectInfo.values else 0)
            w.activated.connect(lambda index: self.updateNodeParameters(selectInfo.values[index], 'value'))
            w.setToolTip(description)
            w.setObjectName(name)
            return w
        inputWidgetVariant = 'PathWidget' if type in filePathTypes else DEFAULT_WIDGET_VARIANT
        w = createInputWidget(
            getPinTypeFromIoType(type),
            lambda value: self.updateNodeParameters(value, 'value'),
            defaultValue,
            inputWidgetVariant
        )
        if w:
            w.setToolTip(description)
            w.blockWidgetSignals(True)
            w.setWidgetValue(defaultValue)
            w.blockWidgetSignals(False)
            w.setObjectName(name)
        return w
    
    def updateNodeParameters(self, value, type):
        parameter = self.node.parameters[self.name]
        parameter[type] = int(value) if parameter['dataType'] == 'integer' else value
        # self.node.inArray.setData(None)
        self.node.dataBeenSet(resetParameters=False)
    
    def changeTypeValue(self, index, sendChanged=True):
        type = None
        data = self.node.inArray.currentData()
        # self.columnNameInput.hide()
        if self.columnSelector is not None:
            self.columnSelector.hide()
        self.inputWidget.hide()
        if index==0:
            # if isinstance(data, pandas.DataFrame):
            #     self.columnSelector.show()
            # else:
            #     self.columnNameInput.show()
            if self.columnSelector is not None:
                self.columnSelector.show()
            type = 'columnName'
        elif index==1:
            self.inputWidget.show()
            type = 'value'
        self.node.parameters[self.name]['type'] = type
        if sendChanged:
            self.node.dataBeenSet(resetParameters=False)
        #     self.node.inArray.setData(None)

    def changeColumnValue(self, index):
        data = self.node.inArray.currentData()
        self.node.parameters[self.name]['columnName'] = data.columns[index]
        self.node.dataBeenSet(resetParameters=False)
        # self.node.inArray.setData(None)

class UIBiitArrayNodeBase(UINodeBase):
    def __init__(self, raw_node):
        super(UIBiitArrayNodeBase, self).__init__(raw_node)
        raw_node.executedChanged.connect(self.executedChanged)
        raw_node.parametersChanged.connect(self.parametersChanged)
    
    def parametersChanged(self, data):
        # print('parametersChanged')
        # self.canvasRef().pyFlowInstance.onRequestFillTable(self)
        if self.isSelected():
            self.canvasRef().tryFillTableView(self)
        
    def executedChanged(self, executed:bool):
        if executed:
            self.headColorOverride = NodeDefaults().PURE_NODE_HEAD_COLOR
            self.headColor = NodeDefaults().PURE_NODE_HEAD_COLOR
        else:
            self.headColorOverride = QtGui.QColor(100, 100, 100, 150)
            self.headColor = QtGui.QColor(100, 100, 100, 150)
    
    def createBaseWidgets(self, propertiesWidget):

        if not self._rawNode.inArray.hasConnections():
            defaultValue = self._rawNode.dataFramePath if self._rawNode.dataFramePath is not None else ''
            inputFilesLayout = QHBoxLayout()
            inputFilesLabel = QLabel('Input files:')
            inputFilesLayout.addWidget(inputFilesLabel)
            self.dataFrameWidget = createInputWidget('StringPin', lambda value: self._rawNode.createDataFrameFromFolder(value), defaultValue, 'PathWidget')
            if self.dataFrameWidget:
                self.dataFrameWidget.setToolTip('Create a DataFrame from files')
                self.dataFrameWidget.blockWidgetSignals(True)
                self.dataFrameWidget.setWidgetValue(defaultValue)
                self.dataFrameWidget.blockWidgetSignals(False)
                self.dataFrameWidget.setObjectName('DataFrameFolder')
            self.dataFrameWidget.le.editingFinished.connect(lambda: self.canvasRef().requestFillProperties.emit(self.createPropertiesWidget))
            inputFilesLayout.addWidget(self.dataFrameWidget)
            propertiesWidget.contentLayout.addLayout(inputFilesLayout)
            
            # self.line = QFrame()
            # self.line.setGeometry(QtCore.QRect(0, 0, 500, 20))
            # self.line.setFrameShape(QFrame.HLine)
            # self.line.setFrameShadow(QFrame.Sunken)
            # propertiesWidget.contentLayout.insertWidget(1, self.line)
        
        return
    
    def createInputWidgets(self, inputsCategory, inGroup=None, pins=True):
        # super(UIBiitArrayNodeBase, self).createInputWidgets(inputsCategory, inGroup, False)
        tool = self._rawNode.__class__.tool
        

        for input in tool.info.inputs:
            iw = ColumnValueWidget(input, self._rawNode, inputsCategory)
            inputsCategory.addWidget(input.name, iw, group=inGroup)
