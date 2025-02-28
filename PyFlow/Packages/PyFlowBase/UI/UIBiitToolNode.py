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
import logging
from qtpy import QtGui
from qtpy.QtWidgets import QWidget, QComboBox, QHBoxLayout, QLabel
from PyFlow.UI.Canvas.UINodeBase import UINodeBase
from PyFlow.UI.Canvas.UICommon import NodeDefaults
from PyFlow.Core.Common import *
from PyFlow.UI.EditorHistory import EditorHistory
from PyFlow.UI.Widgets.InputWidgets import createInputWidget, InputWidgetRaw
from PyFlow.UI.Widgets.PropertiesFramework import CollapsibleFormWidget

class ColumnValueWidget(QWidget):

    ioTypeToPinType = dict(
        string='StringPin',
        float='FloatPin',
        integer='IntPin',
        boolean='BoolPin',
        select='StringPin',
        str='StringPin',
        int='IntPin',
        bool='BoolPin',
    )

    def __init__(self, input, node, parent=None):
        super(ColumnValueWidget, self).__init__(parent=parent)
        self.name = input['name']
        self.inputWidget = self.createInput(self.name, input['type'], input['help'], input.get('default'), input.get('choices'))
        self.node = node
        self.setContentsMargins(0, 0, 0, 0)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.typeSelector = QComboBox()
        self.typeSelector.addItem('Column')
        self.typeSelector.addItem('Value')
        self.layout.addWidget(self.typeSelector)
        self.layout.addWidget(self.inputWidget)
        data = node.getDataFrame()
        type = node.parameters['inputs'][self.name]['type']
        isDataframe = isinstance(data, pandas.DataFrame)
        node.inArray.setClean()
        defaultColumnName = node.parameters['inputs'][self.name]['columnName'] if not isDataframe or node.parameters['inputs'][self.name]['columnName'] in data.columns else data.columns[-1] if len(data.columns)>0 else None
        node.parameters['inputs'][self.name]['columnName'] = defaultColumnName
        # self.layout.addWidget(self.columnNameInput)
        self.typeSelector.activated.connect(self.changeTypeValue)
        # self.columnNameInput.blockWidgetSignals(True)
        # self.columnNameInput.setWidgetValue(defaultColumnName)
        # self.columnNameInput.blockWidgetSignals(False)
        if isinstance(self.inputWidget, InputWidgetRaw):
            if node.parameters['inputs'][self.name]['value'] is not None:
                self.inputWidget.blockWidgetSignals(True)
                self.inputWidget.setWidgetValue(node.parameters['inputs'][self.name]['value'])
                self.inputWidget.blockWidgetSignals(False)
        if isinstance(self.inputWidget, QComboBox):
            self.inputWidget.blockSignals(True)
            self.inputWidget.setCurrentText(node.parameters['inputs'][self.name]['value'])
            self.inputWidget.blockSignals(False)
        self.columnSelector = None
        index = 0 if type == 'columnName' and isDataframe and defaultColumnName is not None else 1
        if isDataframe and not ('static' in input and input['static']) and defaultColumnName is not None:
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
        if 'help' in input:
            self.setToolTip(input['help'])
        else:
            print(input)
            print(node)
            logging.warning(f'Input {input["name"]} of node {node.name} has no help')
    
    def getPinTypeFromIoType(self, ioType):
        return self.ioTypeToPinType[ioType] if ioType in self.ioTypeToPinType else 'StringPin'

    # inputWidgetVariant: PathWidget, FilePathWidget, FolderPathWidget, ObjectPathWidth, EnumWidget
    def createInput(self, name, type, description, defaultValue, selectInfo):
        if type == 'select':
            w = QComboBox()
            for name in selectInfo.names:
                w.addItem(name)
            #TODO
            # for BiitArrayNodes, selectInfo.values is built with Munch with Munch(dict(names=names, values=values)), so it should be a list. 
            # But values has a special meaning in dict, so it is a function instead of a list.
            # So if selectInfo.values is a function: use selectInfo['values'] instead (which is indeed the value list we want)
            selectInfoValues = selectInfo.values if isinstance(selectInfo.values, list) else selectInfo['values']
            w.setCurrentIndex(selectInfoValues.index(defaultValue) if defaultValue in selectInfoValues else 0)
            w.activated.connect(lambda index: self.updateNodeParameterValue(selectInfoValues[index]))
            w.setToolTip(description)
            w.setObjectName(name)
            return w
        inputWidgetVariant = 'PathWidget' if type == 'Path' else DEFAULT_WIDGET_VARIANT
        w = createInputWidget(
            self.getPinTypeFromIoType(type),
            lambda value: self.updateNodeParameterValue(value),
            defaultValue,
            inputWidgetVariant
        )
        if w:
            w.setToolTip(description)
            if defaultValue is not None and defaultValue != '':
                w.blockWidgetSignals(True)
                w.setWidgetValue(defaultValue)
                w.blockWidgetSignals(False)
            w.setObjectName(name)
        return w
    
    def updateNodeParameterValue(self, value):
        parameter = self.node.parameters['inputs'][self.name]
        parameter['value'] = int(value) if 'dataType' in parameter and parameter['dataType'] == 'int' else value
        # self.node.inArray.setData(None)
        self.node.setNodeDirty()
        self.node.compute()
        EditorHistory().saveState("Update parameter", modify=True)
    
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
        self.node.parameters['inputs'][self.name]['type'] = type
        if sendChanged:
            self.node.setNodeDirty()
            self.node.compute()
            EditorHistory().saveState("Update parameter type", modify=True)
        #     self.node.inArray.setData(None)

    def changeColumnValue(self, index):
        data = self.node.inArray.currentData()
        self.node.parameters['inputs'][self.name]['columnName'] = data.columns[index]
        self.node.setNodeDirty()
        self.node.compute()
        EditorHistory().saveState("Update parameter column", modify=True)
        # self.node.inArray.setData(None)

class UIBiitToolNode(UINodeBase):
    def __init__(self, raw_node):
        super(UIBiitToolNode, self).__init__(raw_node)
        raw_node.executedChanged.connect(self.executedChanged)
        raw_node.outArray.dataBeenSet.connect(self.dataBeenSet)
        self.dataFrameWidget = None
    
    def dataBeenSet(self, pin=None):
        if self.isSelected():
            self.canvasRef().tryFillTableView(self)         # Calls TableTool.updateTable()
        
    def executedChanged(self, executed:bool):
        if executed:
            self.headColorOverride = NodeDefaults().PURE_NODE_HEAD_COLOR
            self.headColor = NodeDefaults().PURE_NODE_HEAD_COLOR
        else:
            self.headColorOverride = QtGui.QColor(100, 100, 100, 150)
            self.headColor = QtGui.QColor(100, 100, 100, 150)
    
    def createBaseWidgets(self, propertiesWidget):

        self.dataFrameWidget = None
        if not self._rawNode.inArray.hasConnections():
            defaultValue = '' # self._rawNode.folderDataFramePath if self._rawNode.folderDataFramePath is not None else ''
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
            inputFilesLabel.hide()
            self.dataFrameWidget.hide()
            propertiesWidget.contentLayout.addLayout(inputFilesLayout)
            
            # self.line = QFrame()
            # self.line.setGeometry(QtCore.QRect(0, 0, 500, 20))
            # self.line.setFrameShape(QFrame.HLine)
            # self.line.setFrameShadow(QFrame.Sunken)
            # propertiesWidget.contentLayout.insertWidget(1, self.line)
        
        return
    
    def createInputWidgets(self, inputsCategory, inGroup=None, pins=True):
        # super(UIBiitToolNode, self).createInputWidgets(inputsCategory, inGroup, False)
        tool = self._rawNode.tool
        
        for input in tool.inputs:
            if input.get('advanced'): continue
            iw = ColumnValueWidget(input, self._rawNode, inputsCategory)
            inputsCategory.addWidget(input['name'], iw, group=inGroup)

    def updateOutput(self, output, value):
        output['value'] = value
        self._rawNode.setNodeDirty()
        self._rawNode.compute()
        EditorHistory().saveState("Update parameter", modify=True)

    def createAdvancedCollapsibleFormWidget(self, propertiesWidget):
        advancedInputsCategory = CollapsibleFormWidget(headName="Advanced inputs")

        tool = self._rawNode.tool
        for input in tool.inputs:
            if not input.get('advanced'): continue
            iw = ColumnValueWidget(input, self._rawNode, advancedInputsCategory)
            advancedInputsCategory.addWidget(input['name'], iw)
        if advancedInputsCategory.Layout.count() > 0:
            propertiesWidget.addWidget(advancedInputsCategory)
            advancedInputsCategory.setCollapsed(True)

    def createOutputCollapsibleFormWidget(self, propertiesWidget):
        outputsCategory = CollapsibleFormWidget(headName="Outputs")
        
        for outputName, output in self._rawNode.parameters['outputs'].items():

            w = createInputWidget('StringPin', (lambda value, output=output: self.updateOutput(output, value)), defaultValue=output['defaultValue'])
            if w:
                if 'help' in output:
                    w.setToolTip(output['help'])
                w.blockWidgetSignals(True)
                w.setWidgetValue(output['value'])
                w.blockWidgetSignals(False)
                w.setObjectName(outputName)
                
                # if output is not editable: disable widget
                if output.get('editable') is False: # use "is False" since output.editable can be None, thus "not output.editable" would be True.
                    w.setDisabled(True)

                outputsCategory.addWidget(outputName, w)

        if outputsCategory.Layout.count() > 0:
            propertiesWidget.addWidget(outputsCategory)