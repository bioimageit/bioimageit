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


import json
import os
import uuid
import subprocess
from pathlib import Path
from importlib import import_module, invalidate_caches, reload
from inspect import getfullargspec

from qtpy import QtCore, QtWidgets
from qtpy import QtGui
from qtpy.QtWidgets import *

from PyFlow import getSourcesPath
from PyFlow import GET_PACKAGES, ADD_CLASS
from PyFlow import GET_PACKAGE_PATH

from PyFlow.Core.Common import *
from PyFlow.UI.Canvas.UICommon import *
from PyFlow.UI.EditorHistory import EditorHistory
from PyFlow.Core.NodeBase import NodeBase
from PyFlow.ConfigManager import ConfigManager

class NodeBoxLineEdit(QLineEdit):
    def __init__(self, parent, events=True):
        super(NodeBoxLineEdit, self).__init__(parent)
        self.setParent(parent)
        self._events = events
        self.parent = parent
        self.setLocale(
            QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates)
        )
        self.setObjectName("le_nodes")
        # style = (
        #     "border-radius: 2px;"
        #     + "font-size: 14px;"
        #     + "border-style: outset;"
        #     + "border-width: 1px;"
        # )
        # self.setStyleSheet(style)
        self.setPlaceholderText("enter tool name..")


class NodeBoxTreeWidget(QTreeWidget):
    showInfo = QtCore.Signal(object)
    hideInfo = QtCore.Signal()

    def __init__(
        self,
        parent,
        canvas,
        bNodeInfoEnabled=True,
        useDragAndDrop=True,
        bGripsEnabled=True,
    ):
        super(NodeBoxTreeWidget, self).__init__(parent)
        # style = (
        #     "border-radius: 2px;"
        #     + "font-size: 14px;"
        #     + "border-style: outset;"
        #     + "border-width: 1px;"
        # )
        # self.setStyleSheet(style)
        self.bGripsEnabled = bGripsEnabled
        self.canvas = canvas
        self.setParent(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Sunken)
        self.setObjectName("tree_nodes")
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.setColumnCount(0)
        self.setHeaderHidden(True)
        self.bUseDragAndDrop = useDragAndDrop
        if useDragAndDrop:
            self.setDragEnabled(True)
            self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setAnimated(True)
        self.categoryPaths = {}
        self.bNodeInfoEnabled = bNodeInfoEnabled
        self.currentItemChanged.connect(self.onCurrentItemChanged)
        self.suggestionsEnabled = False
        self.nodeClasses = None

    def onCurrentItemChanged(self, current, previous):
        if current is not None:
            if self.bNodeInfoEnabled:
                if not current.bCategory:
                    if current.docString is not None:
                        self.showInfo.emit(current.docString)
                else:
                    self.hideInfo.emit()

    def _isCategoryExists(self, category_name, categories):
        bFound = False
        if category_name in categories:
            return True
        if not bFound:
            for c in categories:
                sepCatNames = c.split("|")
                if len(sepCatNames) == 1:
                    if category_name == c:
                        return True
                else:
                    for i in range(0, len(sepCatNames)):
                        c = "|".join(sepCatNames)
                        if category_name == c:
                            return True
                        sepCatNames.pop()
        return False

    def addCustomNodeClass(self, workflowPath, nodeName, nodePath:Path):
        toolsPath = str(Path(workflowPath).resolve() / 'Tools')
        if toolsPath not in sys.path:
            sys.path.append(toolsPath)
        moduleImportPath = f'{nodePath.parent.name}.{nodePath.stem}'
        return self.addNodeClass(nodeName, nodePath, moduleImportPath)

    def addNodeClass(self, nodeName, nodePath:Path, moduleImportPath:str):
        from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitToolNode import createNode
        nodeClass = None
        if nodeName in self.nodeClasses:
            # If you are dynamically importing a module that was created since the interpreter began execution (e.g., created a Python source file),
            #  you may need to call invalidate_caches() in order for the new module to be noticed by the import system.
            invalidate_caches()
            nodes = [n for n in self.canvas.getApp().graphManager.get().getAllNodes() if n.__class__.name() == nodeName]
            nodeClass = createNode(nodePath, moduleImportPath, reload(sys.modules[moduleImportPath]))
            for node in nodes:
                node.__class__ = nodeClass
                node.Tool = nodeClass.Tool
        else:
            nodeClass = createNode(nodePath, moduleImportPath, import_module(moduleImportPath))
        if nodeClass is not None:
            self.nodeClasses[nodeName] = nodeClass
            ADD_CLASS('PyFlowBase', nodeName, nodeClass)
            # packages = GET_PACKAGES()
            # packages["PyFlowBase"].addClass(nodeName, node)
        return nodeClass
    
    def removeNodeClass(self, nodeName):
        if nodeName in self.nodeClasses:
            del self.nodeClasses[nodeName]
            self.refresh()
    
    def insertNode(
        self,
        nodeCategoryPath,
        name,
        doc=None,
        libName=None,
        bPyNode=False,
        bCompoundNode=False,
        className=None
    ):
        nodePath = nodeCategoryPath.split("|")[1:]
        categoryPath = ""
        # walk from tree top to bottom, creating folders if needed
        # also writing all paths in dict to avoid duplications
        for folderId in range(0, len(nodePath)):
            folderName = nodePath[folderId]
            if folderId == 0:
                categoryPath = folderName
                if categoryPath not in self.categoryPaths:
                    rootFolderItem = QTreeWidgetItem(self)
                    rootFolderItem.bCategory = True
                    rootFolderItem.setFlags(QtCore.Qt.ItemIsEnabled)
                    rootFolderItem.setText(0, folderName)
                    # rootFolderItem.setBackground(
                    #     folderId, editableStyleSheet().BgColorBright
                    # )
                    self.categoryPaths[categoryPath] = rootFolderItem
            else:
                parentCategoryPath = categoryPath
                categoryPath += "|{}".format(folderName)
                if categoryPath not in self.categoryPaths:
                    childCategoryItem = QTreeWidgetItem(
                        self.categoryPaths[parentCategoryPath]
                    )
                    childCategoryItem.setFlags(QtCore.Qt.ItemIsEnabled)
                    childCategoryItem.bCategory = True
                    childCategoryItem.setText(0, folderName)
                    # childCategoryItem.setBackground(
                    #     0, editableStyleSheet().BgColorBright.lighter(150)
                    # )
                    self.categoryPaths[categoryPath] = childCategoryItem
        # create node under constructed folder
        # TODO: Subclass QTreeWidgetItem to not create dynamic attributes. Below code is ugly
        nodeItem = QTreeWidgetItem(self.categoryPaths[categoryPath])
        nodeItem.bCategory = False
        nodeItem.bPyNode = bPyNode
        nodeItem.bCompoundNode = bCompoundNode
        nodeItem.setText(0, name)
        nodeItem.libName = libName
        nodeItem.className = className if className is not None else name
        nodeItem.docString = doc
        return nodeItem

    def refresh(self, pattern="", pinDirection=None, pinStructure=StructureType.Single, expand='PyFlowBase'):
        self.clear()
        self.categoryPaths = {}

        dataType = None
        if self.canvas.pressedPin is not None:
            dataType = self.canvas.pressedPin.dataType

        for package_name, package in GET_PACKAGES().items():
            # annotated functions
            for libName, lib in package.GetFunctionLibraries().items():
                foos = lib.getFunctions()
                for name, foo in foos.items():
                    foo = foo
                    libName = foo.__annotations__["lib"]
                    fooArgNames = getfullargspec(foo).args
                    fooInpTypes = set()
                    fooOutTypes = set()
                    fooInpStructs = set()
                    fooOutStructs = set()
                    if foo.__annotations__["nodeType"] == NodeTypes.Callable:
                        fooInpTypes.add("ExecPin")
                        fooOutTypes.add("ExecPin")
                        fooInpStructs.add(StructureType.Single)
                        fooOutStructs.add(StructureType.Single)

                    # consider return type if not None
                    if foo.__annotations__["return"] is not None:
                        fooOutTypes.add(foo.__annotations__["return"][0])
                        fooOutStructs.add(
                            findStructFromValue(foo.__annotations__["return"][1])
                        )

                    for index in range(len(fooArgNames)):
                        dType = foo.__annotations__[fooArgNames[index]]
                        # if tuple - this means ref pin type (output) + default value
                        # eg: (3, True) - bool with True default val
                        fooInpTypes.add(dType[0])
                        fooInpStructs.add(findStructFromValue(dType[1]))

                    nodeCategoryPath = "{0}|{1}".format(
                        package_name, foo.__annotations__["meta"][NodeMeta.CATEGORY]
                    )
                    keywords = foo.__annotations__["meta"][NodeMeta.KEYWORDS]
                    checkString = name + nodeCategoryPath + "".join(keywords)
                    if pattern.lower() in checkString.lower():
                        # create all nodes items if clicked on canvas
                        if dataType is None:
                            self.suggestionsEnabled = False
                            self.insertNode(
                                nodeCategoryPath, name, foo.__doc__, libName
                            )
                        else:
                            self.suggestionsEnabled = True
                            if pinDirection == PinDirection.Output:
                                if pinStructure != StructureType.Multi:
                                    hasMultiPins = StructureType.Multi in fooInpStructs
                                    if dataType in fooInpTypes and (
                                        pinStructure in fooInpStructs or hasMultiPins
                                    ):
                                        self.insertNode(
                                            nodeCategoryPath, name, foo.__doc__, libName
                                        )
                                elif dataType in fooInpTypes:
                                    self.insertNode(
                                        nodeCategoryPath, name, foo.__doc__, libName
                                    )
                            else:
                                if pinStructure != StructureType.Multi:
                                    hasMultiPins = StructureType.Multi in fooOutStructs
                                    if dataType in fooOutTypes and (
                                        pinStructure in fooOutStructs or hasMultiPins
                                    ):
                                        self.insertNode(
                                            nodeCategoryPath, name, foo.__doc__, libName
                                        )
                                elif dataType in fooOutTypes:
                                    self.insertNode(
                                        nodeCategoryPath, name, foo.__doc__, libName
                                    )

            # class based nodes
            if self.nodeClasses is None:
                self.nodeClasses = package.GetNodeClasses()
            
            for node_class in self.nodeClasses.values():
                if node_class.__name__ in ("setVar", "getVar"):
                    continue

                nodeCategoryPath = "{0}|{1}".format(package_name, node_class.category())

                nodeName = node_class.title()
                className = node_class.__name__
                checkString = (
                    nodeName
                    + nodeCategoryPath
                    + "".join(node_class.keywords())
                )
                if pattern.lower() not in checkString.lower():
                    continue
                if dataType is None:
                    self.insertNode(
                        nodeCategoryPath, nodeName, node_class.description(), className=className
                    )
                else:
                    # if pressed pin is output pin
                    # filter by nodes input types
                    hints = node_class.pinTypeHints()
                    if pinDirection == PinDirection.Output:
                        if pinStructure != StructureType.Multi:
                            hasMultiPins = StructureType.Multi in hints.inputStructs
                            if dataType in hints.inputTypes and (
                                pinStructure in hints.inputStructs or hasMultiPins
                            ):
                                self.insertNode(
                                    nodeCategoryPath,
                                    nodeName,
                                    node_class.description(),
                                    className=className,
                                )
                        elif dataType in hints.inputTypes:
                            self.insertNode(
                                nodeCategoryPath,
                                nodeName,
                                node_class.description(),
                                className=className,
                            )
                    else:
                        # if pressed pin is input pin
                        # filter by nodes output types
                        if pinStructure != StructureType.Multi:
                            hasMultiPins = StructureType.Multi in hints.outputStructs
                            if dataType in hints.outputTypes and (
                                pinStructure in hints.outputStructs or hasMultiPins
                            ):
                                self.insertNode(
                                    nodeCategoryPath,
                                    nodeName,
                                    node_class.description(),
                                    className=className,
                                )
                        elif dataType in hints.outputTypes:
                            self.insertNode(
                                nodeCategoryPath,
                                nodeName,
                                node_class.description(),
                                className=className,
                            )

            # populate exported py nodes
            packagePath = GET_PACKAGE_PATH(package_name)
            pyNodesRoot = os.path.join(packagePath, "PyNodes")
            if os.path.exists(pyNodesRoot):
                for path, dirs, files in os.walk(pyNodesRoot):
                    for f in files:
                        pyNodeName, extension = os.path.splitext(f)
                        if extension == ".pynode":
                            p = os.path.normpath(path)
                            folders = p.split(os.sep)
                            index = folders.index("PyNodes")
                            categorySuffix = "|".join(folders[index:])
                            category = "{0}|{1}".format(package_name, categorySuffix)
                            self.insertNode(category, pyNodeName, bPyNode=True)

            # populate exported compounds
            compoundNodesRoot = os.path.join(packagePath, "Compounds")
            if os.path.exists(compoundNodesRoot):
                for path, dirs, files in os.walk(compoundNodesRoot):
                    for f in files:
                        _, extension = os.path.splitext(f)
                        if extension == ".compound":
                            compoundsRoot = os.path.normpath(path)
                            fullCompoundPath = os.path.join(compoundsRoot, f)
                            with open(fullCompoundPath, "r") as compoundFile:
                                data = json.load(compoundFile)
                                compoundCategoryName = data["category"]
                                compoundNodeName = data["name"]
                                category = "{0}|{1}|{2}".format(
                                    package_name, "Compounds", compoundCategoryName
                                )
                                self.insertNode(
                                    category, compoundNodeName, bCompoundNode=True
                                )

            # expand all categories
            if dataType is not None:
                for categoryItem in self.categoryPaths.values():
                    categoryItem.setExpanded(True)
            else:
                expandList = expand.split('|')[1:]
                for i in range(1, len(expandList)+1):
                    self.categoryPaths['|'.join(expandList[:i])].setExpanded(True)
            self.sortItems(0, QtCore.Qt.AscendingOrder)

    def mousePressEvent(self, event):
        super(NodeBoxTreeWidget, self).mousePressEvent(event)
        item_clicked = self.currentItem()
        if not item_clicked:
            event.ignore()
            return
        # check if clicked item is a category
        if item_clicked.bCategory:
            event.ignore()
            return
        # find top level parent
        rootItem = item_clicked
        bPyNode = False
        bCompoundNode = False
        if not item_clicked.bCategory:
            bPyNode = rootItem.bPyNode
            bCompoundNode = rootItem.bCompoundNode
        while not rootItem.parent() is None:
            rootItem = rootItem.parent()
            if not rootItem.bCategory:
                bPyNode = rootItem.bPyNode
                bCompoundNode = rootItem.bCompoundNode
        packageName = 'PyFlowBase' # rootItem.text(0)
        pressed_text = item_clicked.text(0)
        libName = item_clicked.libName

        if pressed_text in self.categoryPaths.keys():
            event.ignore()
            return

        jsonTemplate = NodeBase.jsonTemplate()
        jsonTemplate["package"] = packageName
        jsonTemplate["lib"] = libName
        jsonTemplate["type"] = item_clicked.className
        jsonTemplate["name"] = pressed_text
        jsonTemplate["className"] = item_clicked.className
        jsonTemplate["uuid"] = str(uuid.uuid4())
        jsonTemplate["meta"]["label"] = pressed_text
        jsonTemplate["bPyNode"] = bPyNode
        jsonTemplate["bCompoundNode"] = bCompoundNode

        if self.canvas.pressedPin is not None and self.bGripsEnabled:
            a = self.canvas.mapToScene(self.canvas.mouseReleasePos)
            jsonTemplate["x"] = a.x()
            jsonTemplate["y"] = a.y()
            node = self.canvas.createNode(jsonTemplate)
            if bPyNode or bCompoundNode:
                node.rebuild()
            self.canvas.hideNodeBox()
            pressedPin = self.canvas.pressedPin
            if pressedPin.direction == PinDirection.Input:
                for pin in node.UIoutputs.values():
                    wire = self.canvas.connectPinsInternal(pressedPin, pin)
                    if wire is not None:
                        EditorHistory().saveState("Connect pins", modify=True)
                        break
            if pressedPin.direction == PinDirection.Output:
                for pin in node.UIinputs.values():
                    wire = self.canvas.connectPinsInternal(pin, pressedPin)
                    if wire is not None:
                        EditorHistory().saveState("Connect pins", modify=True)
                        break
        else:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()

            pressed_text = json.dumps(jsonTemplate)
            mime_data.setText(pressed_text)
            drag.setMimeData(mime_data)
            drag.exec()

    def update(self):
        # for category in self.categoryPaths.values():
        #     if not category.parent():
        #         category.setBackground(0, editableStyleSheet().BgColorBright)
        #     else:
        #         category.setBackground(
        #             0, editableStyleSheet().BgColorBright.lighter(150)
        #         )
        super(NodeBoxTreeWidget, self).update(self.rootIndex())


class NodeBoxSizeGrip(QSizeGrip):
    """docstring for NodeBoxSizeGrip."""

    def __init__(self, parent=None):
        super(NodeBoxSizeGrip, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(13, 13)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = event.rect()
        painter.setBrush(QtGui.QColor(80, 80, 80, 255))
        painter.drawRoundedRect(rect, 3, 3)
        painter.drawPixmap(rect, QtGui.QPixmap(":resize_diagonal.png"))
        painter.end()


class NodesBox(QFrame):
    """doc string for NodesBox"""

    def __init__(
        self,
        parent,
        canvas,
        bNodeInfoEnabled=True,
        bGripsEnabled=True,
        bUseDragAndDrop=False,
        watchFileChanges=False
    ):
        super(NodesBox, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.bDragging = False
        self.lastCursorPos = QtCore.QPoint(0, 0)
        self.offset = QtCore.QPoint(0, 0)
        self.setMouseTracking(True)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setObjectName("mainLayout")
        self.mainLayout.setSpacing(1)
        self.mainLayout.setContentsMargins(1, 1, 1, 1)
        self.splitter = QSplitter()
        self.splitter.setObjectName("nodeBoxSplitter")
        self.mainLayout.addWidget(self.splitter)
        self.bGripsEnabled = bGripsEnabled
        if self.bGripsEnabled:
            self.sizeGrip = NodeBoxSizeGrip(self)
            self.sizeGrip.setObjectName("nodeBoxSizeGrip")
            self.sizeGripLayout = QHBoxLayout()
            self.sizeGripLayout.setObjectName("sizeGripLayout")
            self.sizeGripLayout.setSpacing(1)
            self.sizeGripLayout.setContentsMargins(1, 1, 1, 1)
            spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            self.sizeGripLayout.addItem(spacerItem)
            self.sizeGripLayout.addWidget(self.sizeGrip)
            self.mainLayout.addLayout(self.sizeGripLayout)

        self.nodeTreeWidget = QWidget()
        self.nodeTreeWidget.setObjectName("nodeTreeWidget")
        self.nodeTreeWidget.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout(self.nodeTreeWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.splitter.addWidget(self.nodeTreeWidget)

        self.lineEdit = NodeBoxLineEdit(self)
        self.lineEdit.setObjectName("lineEdit")

        if not self.bGripsEnabled:
            self.createToolButton = QtWidgets.QPushButton('Create tool')
            self.createToolButton.clicked.connect(self.createTool)
            self.verticalLayout.addWidget(self.createToolButton)

            self.searchLayout = QtWidgets.QHBoxLayout()
            self.searchLabel = QtWidgets.QLabel('Search:')
            self.searchLayout.addWidget(self.searchLabel)
            self.searchLayout.addWidget(self.lineEdit)
            self.verticalLayout.addLayout(self.searchLayout)
        else:
            self.verticalLayout.addWidget(self.lineEdit)
        
        self.lineEdit.textChanged.connect(self.leTextChanged)
        self.nodeInfoWidget = QTextBrowser()
        self.nodeInfoWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.nodeInfoWidget.setObjectName("nodeBoxInfoBrowser")
        self.nodeInfoWidget.setOpenExternalLinks(True)
        self.splitter.addWidget(self.nodeInfoWidget)
        self.splitter.addWidget(self.nodeInfoWidget)
        self.nodeInfoWidget.setVisible(bNodeInfoEnabled)

        self.treeWidget = NodeBoxTreeWidget(
            self, canvas, bNodeInfoEnabled, bUseDragAndDrop, bGripsEnabled
        )
        self.treeWidget.setObjectName("nodeBoxTreeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeWidget)
        self.treeWidget.refresh()

        self.treeWidget.showInfo.connect(self.onShowInfo)
        self.treeWidget.hideInfo.connect(self.onHideInfo)

        if watchFileChanges:
            self.systemWatcher = QtCore.QFileSystemWatcher()
            toolsPath = Path('PyFlow/Tools')
            self.systemWatcher.addPath(str(toolsPath.resolve()))
            self.watchNodes(toolsPath)
            self.systemWatcher.fileChanged.connect(self.fileChanged)
            self.systemWatcher.directoryChanged.connect(self.directoryChanged)

    def fileChanged(self, filePath):
        print('file changed:', filePath)
        filePath = Path(filePath).resolve()
        if filePath.exists():
            if filePath.resolve().is_relative_to(getSourcesPath()):
                self.treeWidget.addNodeClass(filePath.stem, filePath, str(filePath.relative_to(getSourcesPath())).replace('.py', '').replace('/', '.'))
            else:
                self.treeWidget.addCustomNodeClass(self.pyFlowInstance.graphManager.get().workflowPath, filePath.stem, filePath)
            # graphManager = self.pyFlowInstance.graphManager.get()
            # for node in graphManager.getAllNodes():
            #     if node.toolName == filePath.stem and node.process:
            #         print('update node', node, filePath.stem)
            #         node.tool.processDataFrame = nodeClass.process.processDataFrame
            #         node.tool.processData = nodeClass.processData
            self.treeWidget.refresh()
        return
    
    def watchNodes(self, path):
        for file in Path(path).glob('**/*.py'):
            if str(file) not in self.systemWatcher.files():
                print('watch', file)
                self.systemWatcher.addPath(str(file))
        for file in [Path(file) for file in self.systemWatcher.files()]:
            if not file.exists():
                print('remove node', file.resolve())
                self.treeWidget.removeNodeClass(file.stem)

    def directoryChanged(self, path):
        self.watchNodes(path)
    
    def hideEvent(self, event):
        self.bDragging = False

    def showEvent(self, event):
        self.nodeInfoWidget.setHtml("")
        self.bDragging = False

    def onShowInfo(self, restructuredText):
        self.nodeInfoWidget.show()
        self.nodeInfoWidget.setHtml(rst2html(restructuredText))

    def onHideInfo(self):
        self.nodeInfoWidget.setHtml("")

    def sizeHint(self):
        return QtCore.QSize(500, 300)

    def expandCategory(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            if item.text(0) in self.treeWidget.categoryPaths:
                index = self.treeWidget.indexFromItem(item)
                self.treeWidget.setExpanded(index, True)

    def leTextChanged(self):
        if self.lineEdit.text() == "":
            self.lineEdit.setPlaceholderText("enter tool name..")
            self.treeWidget.refresh()
            return
        self.treeWidget.refresh(self.lineEdit.text())
        self.expandCategory()

    def mousePressEvent(self, event):
        super(NodesBox, self).mousePressEvent(event)
        if self.bGripsEnabled:
            if event.pos().y() >= self.geometry().height() - 30:
                self.bDragging = True
                self.lastCursorPos = QtGui.QCursor.pos()

    def mouseMoveEvent(self, event):
        super(NodesBox, self).mouseMoveEvent(event)
        if self.bGripsEnabled:
            if self.bDragging:
                delta = QtGui.QCursor.pos() - self.lastCursorPos
                currentPos = self.pos()
                self.move(currentPos + delta)
                self.lastCursorPos = QtGui.QCursor.pos()

    def mouseReleaseEvent(self, event):
        super(NodesBox, self).mouseReleaseEvent(event)
        self.bDragging = False

    def addCustomNodeClass(self, toolName, toolPath):
        nodeClass = self.treeWidget.addCustomNodeClass(self.pyFlowInstance.graphManager.get().workflowPath, toolName, toolPath)
        self.treeWidget.refresh(expand='PyFlowBase|' + nodeClass.category())
    
    def removeNodeClass(self, toolName):
        return self.treeWidget.removeNodeClass(toolName)
        
    def getTools(self, toolsPath):
        return sorted(list(Path(toolsPath).glob('**/*.py')))
    
    def addTools(self, workflowPath):
        toolsPath = str(workflowPath / 'Tools')
        if toolsPath not in sys.path:
            sys.path.append(toolsPath)
        for toolPath in self.getTools(toolsPath):
            self.addCustomNodeClass(toolPath.stem, toolPath)
        self.watchNodes(toolsPath)
    
    def removeTools(self, workflowPath):
        toolsPath = workflowPath / 'Tools'
        if toolsPath in sys.path:
            sys.path.remove(toolsPath)
        for toolPath in self.getTools(toolsPath):
            self.removeNodeClass(toolPath.stem)
            self.systemWatcher.removePath(str(toolPath))

    def createTool(self):
        rawToolName, ok = QInputDialog.getText(self, 'Tool name dialog', 'Tool name:', QLineEdit.Normal, '')
        if ok and len(rawToolName) > 0:
            # Todo validate tool name
            toolName = rawToolName.replace(' ', '_')
            if toolName in self.treeWidget.nodeClasses.keys():
                QMessageBox.warning(self, 'Name exists', f'Error, the tool {rawToolName} already exists. Please choose a unique tool name.')
                return
            graphManager = self.pyFlowInstance.graphManager.get()
            workflowPath = Path(graphManager.workflowPath).resolve()
            customToolsPath = workflowPath / 'Tools'
            toolPath = customToolsPath / f'biit_{toolName}' / f'{toolName}.py'
            toolPath.parent.mkdir(exist_ok=True, parents=True)
            templatePath = Path('PyFlow/ToolManagement') / 'ToolTemplate.py'
            with open(toolPath, 'w') as destinationFile, open(templatePath, 'r') as exampleFile:
                destinationFile.write(exampleFile.read())

            if str(customToolsPath) not in self.systemWatcher.directories():
                self.systemWatcher.addPath(str(customToolsPath.resolve()))
            if str(toolPath) not in self.systemWatcher.files():
                self.systemWatcher.addPath(str(toolPath))

            self.addCustomNodeClass(toolName, toolPath)

            # Open script file in code editor
            editCmd = ConfigManager().getPrefsValue("PREFS", "General/EditorCmd")
            editCmd = editCmd.replace("@FILE", f'"{toolPath.resolve()}"') if "@FILE" in editCmd else f'{editCmd} {toolPath.resolve()}'
            subprocess.Popen(editCmd, shell=True)
