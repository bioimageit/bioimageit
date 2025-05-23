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
import tempfile
from blinker import Signal
from send2trash import send2trash
from qtpy import QtCore, QtWidgets
from PyFlow import getSourcesPath
from PyFlow import PARAMETERS_PATH, OUTPUT_DATAFRAME_PATH
from PyFlow.ConfigManager import ConfigManager
from PyFlow.UI.Tool.Tool import DockTool
from PyFlow.Packages.PyFlowBase.UI.UIWelcomeDialog import WelcomeDialog
from PyFlow.ThumbnailManagement.ThumbnailGenerator import ThumbnailGenerator
    
class WorkflowTool(DockTool):
    """docstring for Workflow tool."""

    graphFileName = 'workflow.pygraph'
    workflowLoaded = Signal()
    _iconSize = 25

    def __init__(self):
        super(WorkflowTool, self).__init__()
        self.content = None

        self.mainWidget = QtWidgets.QWidget()
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.workflowsWidgetLayout = self.mainLayout

        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.newWorkflowButton = QtWidgets.QPushButton("New workflow")
        self.newWorkflowButton.clicked.connect(lambda clicked: self.createWorkflow())
        self.workflowsWidgetLayout.addWidget(self.newWorkflowButton)

        self.openWorkflowButton = QtWidgets.QPushButton("Open workflow")
        self.openWorkflowButton.clicked.connect(lambda clicked: self.openWorkflow())
        self.workflowsWidgetLayout.addWidget(self.openWorkflowButton)

        self.workflowsWidgetLayout.addWidget(self.listWidget)

        self.renameWorkflowButton = QtWidgets.QPushButton("Rename workflow")
        self.renameWorkflowButton.clicked.connect(lambda clicked: self.renameWorkflow())
        self.workflowsWidgetLayout.addWidget(self.renameWorkflowButton)

        self.duplicateWorkflowButton = QtWidgets.QPushButton("Duplicate workflow")
        self.duplicateWorkflowButton.clicked.connect(lambda clicked: self.duplicateWorkflow())
        self.workflowsWidgetLayout.addWidget(self.duplicateWorkflowButton)

        self.exportWorkflowButton = QtWidgets.QPushButton("Export workflow")
        self.exportWorkflowButton.clicked.connect(lambda clicked: self.exportWorkflow())
        self.workflowsWidgetLayout.addWidget(self.exportWorkflowButton)

        self.deleteWorkflowButton = QtWidgets.QPushButton("Delete workflow")
        self.deleteWorkflowButton.clicked.connect(lambda clicked: self.deleteWorkflow())
        self.workflowsWidgetLayout.addWidget(self.deleteWorkflowButton)

        self.mainLayout.addStretch()

        self.mainWidget.setLayout(self.mainLayout)
        
        self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.setWidget(self.mainWidget)

        self.workflowLoaded.connect(ThumbnailGenerator.get().setWorkflowPathAndLoadImageToThumbnail)

    @staticmethod
    def isMovable():
        return False
    
    @staticmethod
    def isClosable():
        return False
    
    def setAppInstance(self, pyFlowInstance):
        super(WorkflowTool, self).setAppInstance(pyFlowInstance)

        # self.pyFlowInstance.newFileExecuted.connect(self.newFileExecuted)

        workflows = self.getWorkflows()
        if len(workflows) == 0:
            welcomeDialog = WelcomeDialog(self, self)
            welcomeDialog.show()
            welcomeDialog.centerWindow()
            workflows = []
        for workflow in workflows:
            self.addWorkflowToList(workflow, setCurrentItem=False)
        
        # Connect list widget to slots
        self.listWidget.currentItemChanged.connect(self.currentItemChanged)
        self.listWidget.itemSelectionChanged.connect(self.itemSelectionChanged)

        # Load current workflow by setting the current item
        workflow = self.getCurrentWorkflow()
        workflowIndex = self.getWorkflowIndex(workflow) if workflow is not None else 0
        if workflowIndex is None:
            self.addWorkflow(workflow, setCurrentItem=True)
        else:
            self.listWidget.setCurrentRow(workflowIndex)
        if workflow is None and self.listWidget.count()>0:
            workflow = self.listWidget.currentItem().text()
        
        if workflow is not None:
            self.loadWorkflow(workflow, True)

    def getWorkflowIndex(self, workflowPath):
        workflowPath = str(workflowPath)
        workflows = [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        return workflows.index(workflowPath) if workflowPath in workflows else None
    
    def addWorkflowToList(self, path, setCurrentItem=True):
        workflowIndex = self.getWorkflowIndex(path)
        # If path exists in list: select it if setCurrentItem and return
        if workflowIndex is not None:
            if setCurrentItem:
                self.listWidget.setCurrentRow(workflowIndex)
            return self.listWidget.item(workflowIndex)
        newItem = QtWidgets.QListWidgetItem()
        newItem.setText(str(path))
        # newItem.setData(QtCore.Qt.UserRole, workflow['path'])
        self.listWidget.insertItem(self.listWidget.count(), newItem)
        if setCurrentItem:
            self.listWidget.setCurrentItem(newItem)
        if self.listWidget.count() > 1:
            self.deleteWorkflowButton.setDisabled(False)
        return newItem
    
    def addWorkflowToPrefs(self, path):
        # Update settings: update workflows and current workflow
        workflows = self.getWorkflows()
        workflows.append(str(path))
        self.setWorkflows(workflows)
    
    def addWorkflow(self, path, setCurrentItem=True):
        self.addWorkflowToList(path, setCurrentItem)
        self.addWorkflowToPrefs(path)
        if setCurrentItem:
            self.setCurrentWorkflow(path)
        return
    
    def getCurrentWorkflow(self):
        currentWorkflow = ConfigManager().getPrefsValue("PREFS", "General/CurrentWorkflow")
        return Path(currentWorkflow) if currentWorkflow is not None else None
    
    def setCurrentWorkflow(self, path):
        settings = ConfigManager().getSettings("PREFS")
        settings.setValue("General/CurrentWorkflow", str(path))
        Path(path).mkdir(exist_ok=True, parents=True)
        graphManager = self.pyFlowInstance.graphManager.get()
        graphManager.workflowPath = str(path)
        self.workflowLoaded.send(path)
        self.updateNodes(graphManager)

    def updateNodes(self, graphManager):
        # Set nodes dirty since the workflow path has changed, so they must update their outputPath
        nodes = graphManager.getAllNodes()
        for node in nodes:
            node.dirty = True
    
    def getWorkflows(self):
        workflows = ConfigManager().getPrefsValue("PREFS", "General/Workflows")
        return [] if workflows is None else workflows if isinstance(workflows, list) else workflows.split(',')
    
    def setWorkflows(self, workflows):
        settings = ConfigManager().getSettings("PREFS")
        # Remove duplicates and set workflows setting
        settings.setValue("General/Workflows", list(set(workflows)))

    def saveGraphIfShouldSave(self):
        graphManager = self.pyFlowInstance.graphManager.get()
        shouldSave = self.pyFlowInstance.shouldSave()
        if shouldSave == QtWidgets.QMessageBox.Save:
            self.saveGraph(graphManager.workflowPath)
        return shouldSave

    def saveGraph(self, path:Path=None):
        path = self.getCurrentWorkflow() if path is None else Path(path)
        path.mkdir(exist_ok=True, parents=True)
        tmpCurrentFileName = self.pyFlowInstance.currentFileName
        self.pyFlowInstance.currentFileName = str(path / WorkflowTool.graphFileName)
        if not self.pyFlowInstance.save(save_as=False, deleteData=True):
            self.pyFlowInstance.currentFileName = tmpCurrentFileName

    def createWorkflowDialog(self):
        fileName, answer = QtWidgets.QFileDialog.getSaveFileName(self, 'Create workflow directory', options=QtWidgets.QFileDialog.ShowDirsOnly, dir=str(Path.home()))
        if fileName is None or len(fileName) == 0: return None
        path = Path(fileName)
        if path.exists():
            send2trash(path)
        return path

    def createWorkflow(self, path=None, loadWorkflow=False):
        if path is None:
            shouldSave = self.saveGraphIfShouldSave()
            if shouldSave == QtWidgets.QMessageBox.Cancel:
                return
            path = self.createWorkflowDialog()
            if path is None:
                return
        path.mkdir(exist_ok=True, parents=True)

        # Copy .gitignore so that user can easily version his workflow
        shutil.copyfile(getSourcesPath() / 'PyFlow' / 'Scripts' / '.gitignore_template', path / '.gitignore')

        # Update listWidget (add new path and select it) and Update settings (update workflows and set current workflow)
        self.addWorkflow(path)

        if loadWorkflow:
            self.loadWorkflowNoDialog(path)
        # self.saveGraph(path)

        return path
    
    def openWorkflow(self):
        path = self.getCurrentWorkflow()
        shouldSave = self.saveGraphIfShouldSave()
        if shouldSave == QtWidgets.QMessageBox.Cancel:
            return path
        workflowDirectory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Workflow', str(path), QtWidgets.QFileDialog.ShowDirsOnly)
        if workflowDirectory is None or workflowDirectory == '': return
        workflowFile = Path(workflowDirectory) / WorkflowTool.graphFileName
        if not workflowFile.exists():
            # Extracting an archive can lead to a nested directory (especially on Windows)
            # Check if the workflowFolder/workflowFolder/workflow.pygraph exists and use workflowFolder/workflowFolder if so
            nestedWorkflowDirectory = Path(workflowDirectory) / Path(workflowDirectory).name
            workflowFile = nestedWorkflowDirectory / WorkflowTool.graphFileName
            # If workflow file exists in nested folder: use it if parent folder only has one child
            if (not workflowFile.exists()):
                QtWidgets.QMessageBox.warning(self, "Warning: Workflow not found", f'The workflow file "{workflowFile}" does not exist. Please make sure to select a workflow folder.', QtWidgets.QMessageBox.Ok)
                return
            else:
                answer = QtWidgets.QMessageBox.warning(
                    self,
                    "Found nested folder",
                    f'The folder you selected ({workflowDirectory}) is not a workflow folder (it does not contain the {WorkflowTool.graphFileName} file), but it contains a workflow folder ({nestedWorkflowDirectory}). Would you like to load this one instead?',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                )
                if answer == QtWidgets.QMessageBox.No:
                    return
                workflowDirectory = str(nestedWorkflowDirectory)
        self.loadWorkflowNoDialog(workflowDirectory)
        # Update listWidget (add new path and select it) and Update settings (update workflows and set current workflow)
        self.addWorkflow(workflowDirectory, setCurrentItem=True)
        return workflowDirectory
    
    def renameWorkflow(self):
        path = self.getCurrentWorkflow()

        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Create new workflow directory', options=QtWidgets.QFileDialog.ShowDirsOnly, dir=str(path.parent))
        if fileName is None or len(fileName) == 0: return None
        newPath = Path(fileName)
        if newPath.exists():
            QtWidgets.QMessageBox.warning(self, "Warning: directory exists", f'The directory "{newPath}" exists, it will be sent to the trash.', QtWidgets.QMessageBox.Ok)
            send2trash(newPath)
        
        # Rename directory
        shutil.move(path, newPath)  # use shutil.move(path, newPath) instead of path.rename(newPath) in case the newPath is on a different filesystem
        
        # Update listWidget: remove old path & add new path
        for item in self.listWidget.findItems(str(path), QtCore.Qt.MatchExactly):
            self.listWidget.takeItem(self.listWidget.row(item))
        self.addWorkflowToList(newPath, setCurrentItem=True)

        # Update settings: update workflows and current workflow
        workflows = [w for w in self.getWorkflows() if str(w) != str(path)]
        workflows.append(str(newPath))
        self.setWorkflows(workflows)
        self.setCurrentWorkflow(newPath)
        self.saveGraph(newPath)
        return
    
    def duplicateWorkflow(self):
        path = self.getCurrentWorkflow()
        newPath = self.createWorkflow()
        if newPath is None: return
        send2trash(newPath)
        shutil.copytree(path, newPath)
        return

    def removeExternalPaths(self):
        import json
        with open(self.pyFlowInstance.currentFileName, 'r') as f:
            graph = json.load(f)
            for node in graph['nodes']:
                if 'folderDataFramePath' in node:
                    node['folderDataFramePath'] = None
                # Todo: check parameters
        with open(self.pyFlowInstance.currentFileName, 'w') as f:
            json.dump(graph, f)
        return
    
    def exportWorkflow(self):
        path = self.getCurrentWorkflow()
        self.saveGraph(path)
        self.removeExternalPaths()
        zipFilePath, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Workflow (create .zip file)', dir= str(path.parent / f'{path.name}.zip'), filter='Zip files (*.zip)')
        if zipFilePath is None or len(zipFilePath) == 0: return
        zipFilePath = Path(zipFilePath)
        if zipFilePath.exists():
            QtWidgets.QMessageBox.warning(self, "Warning: file exists", f'The file "{zipFilePath}" exists, it will be sent to the trash.', QtWidgets.QMessageBox.Ok)
            send2trash(zipFilePath)
        with tempfile.TemporaryDirectory() as tmp:
            workflowFolder = Path(tmp) / zipFilePath.stem
            workflowFolder.mkdir(parents=True, exist_ok=True)
            # Copy the Tools and Scripts folder
            for name in ['Tools', 'Scripts']:
                if (path / name).exists():
                    shutil.copytree(path / name, workflowFolder / name, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
            # Copy parameters.json and output_data_frame.csv files (PARAMETERS_PATH, OUTPUT_DATAFRAME_PATH) in the "Data / nodeName" folders, but not the other data files
            if (path / 'Metadata').exists():
                metadataFolder = workflowFolder / 'Metadata'
                metadataFolder.mkdir()
                for folder in sorted(list((path / 'Metadata').iterdir())):
                    (metadataFolder / folder.name).mkdir()
                    for fileName in [PARAMETERS_PATH, OUTPUT_DATAFRAME_PATH]:
                        if (folder / fileName).exists():
                            shutil.copyfile(folder / fileName, metadataFolder / folder.name / fileName)
            shutil.copyfile(path / WorkflowTool.graphFileName, workflowFolder / WorkflowTool.graphFileName)
            shutil.make_archive(zipFilePath.with_suffix(''), 'zip', tmp)
        return
    
    def deleteWorkflow(self, askConfirmation=True):
        if self.listWidget.count() > 1:
            row = self.listWidget.currentRow()
            item = self.listWidget.currentItem()
            answer = QtWidgets.QMessageBox.warning(
                self,
                "Confirm?",
                f'Do you want to send the workflow folder "{item.text()}" to the trash?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            ) if askConfirmation else QtWidgets.QMessageBox.Yes
            if answer == QtWidgets.QMessageBox.Yes:
                send2trash(item.text())
            self.listWidget.takeItem(row)
            workflows = [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
            self.setWorkflows(workflows)
            if self.listWidget.count == 1:
                self.deleteWorkflowButton.setDisabled(True)
        return
    
    def currentItemChanged(self, current, previous):
        if current is None: return # current is None when the list is empty: for example when user renames the only workflow
        # path = current.data(QtCore.Qt.UserRole)
        path = Path(current.text())
        # Ask to save current workflow: load if user saves or discard, return to previous item if user cancels
        if not self.loadWorkflow(path):
            QtCore.QTimer.singleShot(0, lambda: self.listWidget.setCurrentItem(previous))
        return

    # Reselect the first item if the selection is empty
    def itemSelectionChanged(self):
        if len(self.listWidget.selectedItems()) == 0:
            self.listWidget.setCurrentItem(self.listWidget.item(0))
    
    def loadWorkflow(self, path, force=False):
        if self.getCurrentWorkflow() == path and not force: return True
        shouldSave = self.saveGraphIfShouldSave()
        if shouldSave == QtWidgets.QMessageBox.Cancel:
            return False
        self.loadWorkflowNoDialog(path)
        return True

    def loadWorkflowNoDialog(self, path):
        path = Path(path)
        if self.pyFlowInstance is None: return
        self.removeCustomTools(self.getCurrentWorkflow())
        self.setCurrentWorkflow(path)

        if not (path / WorkflowTool.graphFileName).exists():
            self.pyFlowInstance.modified = False
            # self.pyFlowInstance._clickNewFile()
            self.pyFlowInstance.newFile()
            self.saveGraph(path)
        
        # self.workflowPathWidget.setWidgetValue(path)
        
        self.loadCustomTools(path)

        self.pyFlowInstance.loadFromFile(str(path / WorkflowTool.graphFileName))
        self.pyFlowInstance.modified = False
        self.pyFlowInstance.updateLabel()
        return

    def loadCustomTools(self, path=None):
        path = self.getCurrentWorkflow() if path is None else Path(path)
        if path is None: return
        for nodeBox in self.pyFlowInstance.getRegisteredTools(classNameFilters=["NodeBoxTool"]):
            nodeBox.content.addTools(path)
        return
    
    def removeCustomTools(self, path=None):
        path = self.getCurrentWorkflow() if path is None else Path(path)
        if path is None: return
        for nodeBox in self.pyFlowInstance.getRegisteredTools(classNameFilters=["NodeBoxTool"]):
            nodeBox.content.removeTools(path)
        return
    
    def onShow(self):
        super(WorkflowTool, self).onShow()
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
        return "Workflow"

    @staticmethod
    def name():
        return "Workflow"
