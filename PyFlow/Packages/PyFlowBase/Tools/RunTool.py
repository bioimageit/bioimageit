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

from typing import Iterable
from pathlib import Path
import json, copy
import re
import shutil
import platform
import threading
import copy
from os import linesep
import traceback

# import bioimageit_core.api as iit
# from bioimageit_formats import FormatsAccess
import pandas

from qtpy import QtGui, QtCore
from qtpy.QtCore import QObject, QThread
from qtpy.QtWidgets import *

from PyFlow.UI.Tool.Tool import ShelfTool
from PyFlow.UI.Widgets import BlueprintCanvas
from PyFlow.Packages.PyFlowBase.Tools import RESOURCES_DIR
from PyFlow.Packages.PyFlowBase.Nodes.script import ScriptNode
from PyFlow.Packages.PyFlowBase.Tools.LoggerTool import LoggerTool
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitNodeBase import BiitNodeBase
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitSimpleITKNodes import SimpleITKBase
from PyFlow.Packages.PyFlowBase.FunctionLibraries.PandasLib import PandasLib, ListFiles
from PyFlow.Packages.PyFlowBase.FunctionLibraries.OmeroLib import OmeroLib, OmeroDownload, OmeroUpload, OmeroBase
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitUtils import getOutputFolderPath
from PyFlow.Core.OmeroService import OmeroService
from PyFlow.invoke_in_main import inmain, inthread

def dedent(message):
    return linesep.join(line.lstrip().replace('[t]', '\t') for line in message.splitlines())

class ProgressDialog(QWidget):

    allNodesProcessedMessage = 'All nodes were processed.'

    def __init__(self, runTool):
        super().__init__(runTool.pyFlowInstance)
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 500, 75)
        self.layout = QVBoxLayout(self)
        self.label = QLabel('Running', parent=self)

        self.logView = QTextBrowser()
        self.logView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        # self.logView.setOpenLinks(False)
        self.logView.setReadOnly(True)

        self.cancelButton = QPushButton('Cancel execution', parent=self)
        self.cancelButton.clicked.connect(runTool.cancel)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.pbar)
        self.layout.addWidget(self.logView)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 550, 100)
        self.setWindowTitle('Progress Bar')
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.nodeName = None
        self.currentNode = 0    # The number of the node being processed
        self.currentRow = 0     # The number of the dataFrame row being processed for this node
        self.currentStep = 0    # The number of the step being executed for this tool
        self.nNodes = 0         # The number of nodes to process
        self.nRows = 0          # The number of dataFrame rows to process for this node
        self.nSteps = 0         # The number of steps for this tool

    def progress(self, label, value):
        self.label.setText(label)
        self.pbar.setValue(value)

    def resetProgressPercentage(self):
        self.currentNode = 0
        self.currentRow = 0
        self.currentStep = 0
        self.nNodes = None
        self.nRows = None
        self.nSteps = None

    def getProgressPercentage(self):
        if self.nNodes is None or self.nNodes == 0: return 0
        nodePercentage = 100.0 / self.nNodes
        percentage = self.currentNode * nodePercentage
        if self.nRows is None: return percentage
        percentage += self.currentRow * nodePercentage / self.nRows
        if self.nSteps is None: return percentage
        rowPercentage = nodePercentage / self.nRows
        percentage += self.currentStep * rowPercentage / self.nSteps
        return percentage
    
    def logProgress(self, message=None, percentage=None):
        percentage = self.getProgressPercentage() if percentage is None else percentage
        message = f'Running node {self.nodeName} ({self.currentNode+1} / {self.nNodes})' if message is None else message
        inmain(lambda: self.progress(message, int(percentage)))
    
    def parseInts(self, tuple):
        return [int(v) for v in tuple]
    
    def log(self, message):
        if message == self.allNodesProcessedMessage:
            inmain(lambda: self.progress(message, int(100)))
        # Find progess prints: string in the format [[current/total]] where current is the current node, row or process step ; and total the total number of nodes, rows or process steps.
        progressPrints = re.findall(r'\[\[(\d)\/(\d)\]\]', message)
        if len(progressPrints) > 0:
            # Remove the [[ and ]] sequences from message
            message = re.sub(r'\[\[|\]\]', '', message)
            if message.startswith('Process node'):
                self.nodeName = message.split(': ')[-1]
                self.currentNode, self.nNodes = self.parseInts(progressPrints[0])
            elif message.startswith('Process row'):
                self.currentRow, self.nRows = self.parseInts(progressPrints[0])
            else:
                self.currentStep, self.nSteps = self.parseInts(progressPrints[0])
            self.logProgress()
        inmain(lambda: self.logView.append(message))

class RunTool(ShelfTool):
    """docstring for RunTool."""

    req = None
    cancelExecution = threading.Event()

    def __init__(self, initialize=True):
        super(RunTool, self).__init__()
        if not initialize: return
        
        # if RunTool.req is None:
        #     RunTool.req = iit.Request('biit/config.json')
        #     RunTool.req.connect()

        self.executing = False
        self.logTool = None
        self.currentNode = None
        self.progressDialog = ProgressDialog(self)
        BiitNodeBase.log.connect(self.log)

    @staticmethod
    def toolTip():
        return "Execute unexecuted nodes"

    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "biit/play-large-fill.svg")

    @staticmethod
    def name():
        return "Run"
    
    @staticmethod
    def createUuidToNodes(nodes):
        RunTool.uuidToNodes = { str(node.uid): node for node in nodes}
        return RunTool.uuidToNodes
    
    @staticmethod
    def isBiitLib(node):
        return node.lib == 'BiitLib'
    
    @staticmethod
    def wasExecuted(node):
        return hasattr(node, 'executed') and node.executed
    
    @staticmethod
    def isPlanned(node):
        return hasattr(node, 'planned') and node.planned

    @staticmethod
    def mustExecute(node):
        return RunTool.isBiitLib(node) and not RunTool.wasExecuted(node)
    
    def getNodesToExecute(self, nodes):
        return [ node for node in nodes if RunTool.mustExecute(node) ]

    @staticmethod
    def getInputNodes(node):
        return [outputPin.owningNode() for inputPin in node.inputs.values() for outputPin in inputPin.affected_by]
    
    @staticmethod
    def inputsWereExecuted(node):
        return len(node.inputs) == 0 or all([not RunTool.isBiitLib(n) or RunTool.wasExecuted(n) for n in RunTool.getInputNodes(node)])
    
    @staticmethod
    def inputsArePlanned(node):
        return len(node.inputs) == 0 or all([not RunTool.isBiitLib(n) or RunTool.isPlanned(n) for n in RunTool.getInputNodes(node)])
    
    @staticmethod
    def getItem(list, value, key='name', cond=None, default=None):
        return next(filter(cond if cond is not None else lambda i: i[key] == value, list), default)
    
    @staticmethod
    def getItemFromAttr(list, value, key='name', default=None):
        return RunTool.getItem(list, value, cond=lambda i: getattr(i, key) == value, default=default)

    @staticmethod
    def getInfoFromLabel(ios, label):
        return RunTool.getItemFromAttr(ios, label, 'description')
    
    @staticmethod
    def getInfoFromIo(ioInfos, nodeIo):
        return RunTool.getInfoFromLabel(ioInfos, nodeIo.name)
    
    # Returns True if the node was executed, False else (if inputs were not executed, wait for previous nodes to execute)
    @staticmethod
    def execute(node):
        if not RunTool.inputsWereExecuted(node): return False
        node.compute()

        
        if node.__class__.__name__ in PandasLib.classes.keys():
            node.executed = True
            return True
        if node.__class__.__name__ in OmeroLib.classes.keys() or isinstance(node, SimpleITKBase) or isinstance(node, ScriptNode):
            node.execute()
            return True
        
        node.execute(RunTool.req)

        return True

    def do(self):
        self.run()
    
    def planExecution(self, node):
        if not RunTool.inputsArePlanned(node): return False
        node.planned = True
        return True
    
    def resetPlanned(self, nodes):
        for node in nodes:
            node.planned = False
        return
    
    def displayError(self, exception, traceback):
        message = QMessageBox(self.pyFlowInstance)
        message.setWindowTitle('Error during execution')
        text = f'{exception}'
        message.setText(text)
        self.log('Error during execution:')
        self.log(text)
        message.setDetailedText(f'{traceback}')
        message.exec()

    def initializeLog(self):
        logTools = [tool for tool in self.pyFlowInstance._tools if isinstance(tool, LoggerTool)]
        self.logTool = logTools[0] if len(logTools)>0 else None
    
    def log(self, message:str):
        print(message)
        self.progressDialog.log(message)
        if self.logTool is None: return
        inmain(lambda: self.logTool.logPython(message))
        return
    
    def run(self):
        print('Run')
        self.cancelExecution = threading.Event()

        self.progressDialog.resetProgressPercentage()
        self.progressDialog.progress('Starting environment...', 0)
        self.progressDialog.show()

        # self.progressDialog.logView.append('Starting environment...')
        graphManager = self.pyFlowInstance.graphManager.get()
        nodes = graphManager.getAllNodes()
        nodesToExecute = set(self.getNodesToExecute(nodes))
        
        self.initializeLog()
        self.createUuidToNodes(nodes)

        self.resetPlanned(nodesToExecute)
        plannedNodes = []
        while len(nodesToExecute)>0:
            lastN = len(nodesToExecute)
            for node in nodesToExecute.copy():
                if self.planExecution(node):
                    plannedNodes.append(node)
                    nodesToExecute.remove(node)
            if len(nodesToExecute) == lastN:
                QMessageBox.warning(self.pyFlowInstance, "Cycle in the graph", "There is a cycle in the graph, some nodes cannot be executed.")
                return
        self.executionThread = inthread(self.executeNodes, plannedNodes)
        # self.executeNodes(plannedNodes, logTool, progress)

    def executeNodes(self, plannedNodes):

        self.executing = True
        try:
            for n, node in enumerate(plannedNodes):
                self.log(f'Process node [[{n}/{len(plannedNodes)}]]: {node.name}')
                self.currentNode = node
                self.execute(node)
                if self.cancelExecution.is_set(): break
            self.log(self.progressDialog.allNodesProcessedMessage)
            inmain(self.saveGraph)
            inmain(lambda: self.progressDialog.hide())
        except Exception as e:
            print(e.args[0]['exception'] if isinstance(e, Iterable) and len(e.args)>0 and 'exception' in e.args[0] else e)
            tb = e.args[0]['traceback'] if isinstance(e, Iterable) and len(e.args)>0 and 'traceback' in e.args[0] else ''
            tb += '\n\n\n'
            print(tb)
            traceback.print_tb(e.__traceback__)
            tb += '\n'.join(traceback.format_tb(e.__traceback__))
            inmain(lambda: self.displayError(e, tb))
        
        self.executing = False
        self.cancelExecution.clear()
        return
    
    def cancel(self):
        if not self.executing:
            self.progressDialog.hide()
        else:
            self.cancelExecution.set()
            if self.currentNode is not None:
                self.currentNode.exitTool()
    
    def saveGraph(self):
        graphManager = self.pyFlowInstance.graphManager.get()
        with open(Path(graphManager.workflowPath) / 'workflow.pygraph', "w") as f:
            saveData = graphManager.serialize()
            json.dump(saveData, f, indent=4)
    
class RunAllTool(RunTool):
    """docstring for RunAllTool."""

    def __init__(self):
        super(RunAllTool, self).__init__(False)

    @staticmethod
    def toolTip():
        return "Execute all nodes"
    
    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "biit/speed-fill.svg")
    
    @staticmethod
    def name():
        return "Run all"
    
    def do(self):
        graphManager = self.pyFlowInstance.graphManager.get()
        for node in graphManager.getAllNodes():
            if RunTool.isBiitLib(node):
                node.setExecuted(False)
        super(RunAllTool, self).do()

class RunSelectedTool(RunTool):
    """docstring for RunSelectedTool."""

    def __init__(self):
        super(RunSelectedTool, self).__init__(False)

    @staticmethod
    def toolTip():
        return "Execute selected nodes"
    
    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "biit/play-large-line.svg")
    
    @staticmethod
    def name():
        return "Run selected"
    
    def getNodesToExecute(self, nodes):
        canvas: BlueprintCanvas = self.pyFlowInstance.getCanvas()
        selectedNodes = canvas.selectedNodes()
        return [ node for node in nodes if RunTool.mustExecute(node) and node in selectedNodes ]


class ExportWorkflowTool(ShelfTool):
    """docstring for ExportRunTool."""

    def __init__(self):
        super(ExportWorkflowTool, self).__init__()

    @staticmethod
    def toolTip():
        return "Export NextFlow workflow"
    
    @staticmethod
    def getIcon():
        return QtGui.QIcon(RESOURCES_DIR + "biit/nextflow.png")
    
    @staticmethod
    def name():
        return "Export NextFlow workflow"
    
    def getActivateCommand(self, name):
        
        is_windows = platform.system() == 'Windows'
        conda_path = Path(self.conda_dir)
        activate_path = conda_path / 'condabin' / 'conda.bat' if is_windows else conda_path / 'etc' / 'profile.d' / 'conda.sh'
        return f'"{activate_path}" activate {name}' if is_windows else f'. "{activate_path}" && conda activate {name}'

    # def exportNextFlowNodeBckp(self, node, processes):
    #     if not (isinstance(node, ListFiles) or isinstance(node, BiitArrayNodeBase)): return

    #     # Get input files if any
    #     if isinstance(node, ListFiles):
    #         channel = f"def {node.name}_{node.columnNamePin.currentData()} = Channel.fromPath( '{node.pathPin.currentData()}' )"
    #     if isinstance(node, BiitArrayNodeBase) and not node.inArray.hasConnections() and isinstance(node.getDataFrame(), pandas.DataFrame):
    #         channel = f"def {node.name}_path = Channel.fromPath( '{node.dataFramePath}' )"

    #     # Create processes
    #     tool = node.__class__.tool
    #     name = tool.info.id if tool is not None else node.name
    #     if name not in processes:
    #         activate_command = self.getActivateCommand(self, name)
    #         argsList = RunTool.getArgs(tool.info, node)
    #         argsList = argsList if type(argsList) is list else [argsList]
    #         preparedArgs = [RunTool.req._prepare_command(tool, args) for args in argsList]
    #         commands = [activate_command] + [' '.join(arg_list) for arg_list in preparedArgs]
    #         inputs = '\n'.join([('path' if isIoPath(input) else 'val')+f': {input.name}' for input in tool.info.inputs])
    #         outputs = '\n'.join([('path' if isIoPath(output) else 'val')+f': {output.name}' for output in tool.info.outputs])
    #         scripts = '\n'.join(commands)
    #         processes[name] = f"""process {name} {{
    #                 {inputs}
    #                 {outputs}
    #                 {scripts}
    #         }}
            
    #         """

    #     # Launch them in order
    #     # executions = f'{} = {}({})'
    #     return

    def exportToolDescription(self, nodeName, tool, outputFolder, workflowPath):
        descriptionPath = outputFolder / 'description.json'
        with open(descriptionPath, 'w') as f:
            toolInfo = { key: value for key, value in tool.info.__dict__.items() if key not in ['inputs', 'outputs', 'requirements', 'tests', 'uri'] }
            toolInfo['inputs'] = []
            for input in tool.info.__dict__['inputs']:
                toolInfo['inputs'].append({ key: value for key, value in input.__dict__.items() if key not in ['select_info']})
            toolInfo['outputs'] = []
            for output in tool.info.__dict__['outputs']:
                toolInfo['outputs'].append({ key: value for key, value in output.__dict__.items() if key not in ['select_info']})
            toolInfo['node_name'] = nodeName
            toolInfo['workflow_path'] = str(workflowPath)
            json.dump(toolInfo, f)
        return descriptionPath.relative_to(workflowPath)

    def exportDataFrame(self, node, outputFolder, workflowPath):
        dataFramePath = outputFolder / 'input_data_frame.csv'
        dataFrame = node.getDataFrame()
        if isinstance(dataFrame, pandas.DataFrame):
            dataFrame.to_csv(dataFramePath)
            return dataFramePath.relative_to(workflowPath)
        else:
            raise Exception(f'Error: the input data frame of node "{node.name}" is empty wheares it has input connections.')
    
    def getPreviousDataFrame(self, node):
        return f'{node.getPreviousNode().name}_out_data_frame'
    
    def exportParameters(self, parameters, outputFolder, workflowPath):
        parametersPath = outputFolder / 'parameters.json'
        with open(parametersPath, 'w') as f:
            json.dump(parameters, f)
        return parametersPath.relative_to(workflowPath)
    
    def exportNextFlowNode(self, node, processes, executions):
        
        graphManager = self.pyFlowInstance.graphManager.get()

        tool = node.__class__.tool if hasattr(node.__class__, 'tool') else None
        # name = tool.info.id if tool is not None else node.name

        # Create processes
        outputFolder = getOutputFolderPath(node.name)
        outputFolder.mkdir(exist_ok=True, parents=True)

        if node.__class__.__name__ in OmeroLib.classes.keys():

            if isinstance(node, OmeroDownload):

                # if name not in processes:
                inputs = '''val dataset_name
                [t]val node_name'''
                outputs = 'path "output_data_frame.csv"\n'
                host, port, username = OmeroService().getSettings()
                omero_commands = f'--omero_host {host} --omero_port {port} --omero_user {username}'
                scripts = '''source $params.conda_path/etc/profile.d/conda.sh
                [t]conda activate bioimageit
                [t]python $projectDir/nf_omero.py ''' + omero_commands + ''' download --dataset_name ${dataset_name} --node_name ${node_name}'''
                processes[node.name] = dedent(f'''process {node.name} {{
                [t]publishDir '{node.name}'
                [t]
                [t]input:
                [t]{inputs}
                [t]
                [t]output:
                [t]{outputs}
                [t]
                [t]script:
                [t]"""
                [t]{scripts}
                [t]"""
                }}
                ''')

                inputPath = node.datasetPin.getData()

                # Launch them in order
                execution = f'{node.name}_out_data_frame = {node.name}("{inputPath}", "{node.name}")'
                executions.append(execution)

            elif isinstance(node, OmeroUpload):

                # if name not in processes:
                inputs = '''val dataset_name
                [t]val project_name
                [t]path input_data_frame
                [t]val column_name
                [t]val meta_data_columns'''
                host, port, username = OmeroService().getSettings()
                omero_commands = f'--omero_host {host} --omero_port {port} --omero_user {username}'
                scripts = '''source $params.conda_path/etc/profile.d/conda.sh
                [t]conda activate bioimageit
                [t]python $projectDir/nf_omero.py ''' + omero_commands + ''' upload --dataset_name ${dataset_name} --project_name ${project_name} --data_frame ${input_data_frame} --column_name ${column_name} --meta_data_columns ${meta_data_columns}'''
                processes[node.name] = dedent(f'''process {node.name} {{
                [t]publishDir '{node.name}'
                [t]
                [t]input:
                [t]{inputs}
                [t]
                [t]script:
                [t]"""
                [t]{scripts}
                [t]"""
                }}
                ''')
                
                dataframePath = self.getPreviousDataFrame(node) # f'"$projectDir/{self.exportDataFrame(node, outputFolder, graphManager.workflowPath)}"'
                datasetName = node.datasetPin.currentData()
                projectName = node.projectPin.currentData()
                metaDataColumns = [mdc for mdc in node.metaDataColumnsPin.currentData().split(',') if len(mdc)>0]
                columnName = node.columnName if node.columnName is not None else node.getDataFrame().columns[-1] if node.getDataFrame() is not None else None

                # Launch them in order
                execution = f'{node.name}_out_data_frame = {node.name}("{datasetName}", "{projectName}", {dataframePath}, "{columnName}", "{metaDataColumns}")'
                executions.append(execution)
            return
        
        if isinstance(node, ListFiles):
            
            # if name not in processes:
            inputs = '''path input_path
            [t]val column_name'''
            outputs = 'path "output_data_frame.csv"'
            scripts = 'python $projectDir/nf_list_files.py --input_path ${input_path} --column_name ${column_name} --output_path "output_data_frame.csv"'
            processes[node.name] = dedent(f'''process {node.name} {{
            [t]publishDir '{node.name}'
            [t]
            [t]input:
            [t]{inputs}
            [t]
            [t]output:
            [t]{outputs}
            [t]
            [t]script:
            [t]"""
            [t]{scripts}
            [t]"""
            }}
            ''')

            inputPath = node.pathPin.getData()
            columnName = node.columnNamePin.getData()

            # Launch them in order
            execution = f'{node.name}_out_data_frame = {node.name}("{inputPath}", "{columnName}")'
            executions.append(execution)
            return
        
        # Todo: other nodes: Omero nodes, Pandas nodes (concat), Python node
        if not isinstance(node, BiitArrayNodeBase): return


        # Only export data frame if input inArray is not connected: in this case we must have the input source ; 
        # otherwise it will be given from the preview node
        dataframePath = f'"$projectDir/{self.exportDataFrame(node, outputFolder, graphManager.workflowPath)}"' if not node.inArray.hasConnections() else self.getPreviousDataFrame(node)
        descriptionPath = f'$projectDir/{self.exportToolDescription(node.name, tool, outputFolder, graphManager.workflowPath)}'
        parametersPath = f'$projectDir/{self.exportParameters(node.parameters, outputFolder, graphManager.workflowPath)}'

        # if name not in processes:         

        # inputs = textwrap.dedent("""\
        # inputs = inspect.cleandoc("""path input_data_frame
        inputs = '''path input_data_frame
        [t]path description
        [t]path parameters'''
        outputs = 'path "output_data_frame.csv"\n'
        # for output in tool.info.outputs:
        #     outputs += f'[t]path "{output.name}*.{FormatsAccess.instance().get(output.type).extension}"\n'
        # Todo: make it Windows compatible
        scripts = '''source $params.conda_path/etc/profile.d/conda.sh
        [t]conda activate bioimageit
        [t]python $projectDir/nf_process.py --data_frame ${input_data_frame} --node_description ${description} --node_parameters ${parameters} --config_file $params.biit_config_path''' #  --output_path $PWD '''
        # processes[name] = inspect.cleandoc(f'''process {name} {{
        processes[node.name] = dedent(f'''process {node.name} {{
        [t]publishDir '{node.name}'
        [t]
        [t]input:
        [t]{inputs}
        [t]
        [t]output:
        [t]{outputs}
        [t]script:
        [t]"""
        [t]{scripts}
        [t]"""
        }}
        ''')

        # Launch them in order
        execution_outputs = ''
        # for output in tool.info.outputs:
        #     execution_outputs += f', {node.name}_{output.name}'
        execution = f'({node.name}_out_data_frame{execution_outputs}) = {node.name}({dataframePath}, "{descriptionPath}", "{parametersPath}")'
        executions.append(execution)
        return

    def getInputNodes(self, node):
        return [RunTool.uuidToNodes[connection['lhsNodeUid']] for input in node.inputs.values() for connection in input.linkedTo]
    
    def inputsWereProcessed(self, node, nodesToProcess):
        return len(node.inputs) == 0 or all([not RunTool.isBiitLib(n) or (n not in nodesToProcess) for n in RunTool.getInputNodes(node)])
    
    def copyDependencies(self, graphManager):
        pyflowPath = Path(__file__).parent.parent.parent.parent.parent
        outputPath = Path(graphManager.workflowPath)

        biitConfigRef = pyflowPath / 'biit' / 'config.json'
        biitConfig: Path = outputPath / 'biit_config.json'
        shutil.copyfile(biitConfigRef, biitConfig)

        with open(biitConfig, 'r') as f:
            bc = json.load(f)
            condaPath = bc['runner']['conda_dir']
            
        biitConfigPath = f'$projectDir/{biitConfig.relative_to(outputPath)}'
        
        nfProcessRef = pyflowPath / 'PyFlow' / 'Scripts' / 'nf_process.py'
        nfProcess = outputPath / nfProcessRef.name
        shutil.copyfile(nfProcessRef, nfProcess)
        nfProcessPath = f'$projectDir/{nfProcess.relative_to(outputPath)}'

        nfListFilesRef = pyflowPath / 'PyFlow' / 'Scripts' / 'nf_list_files.py'
        nfListFiles = outputPath / nfListFilesRef.name
        shutil.copyfile(nfListFilesRef, nfListFiles)
        nfListFilesPath = f'$projectDir/{nfListFiles.relative_to(outputPath)}'

        nfOmeroRef = pyflowPath / 'PyFlow' / 'Scripts' / 'nf_omero.py'
        nfOmero = outputPath / nfOmeroRef.name
        shutil.copyfile(nfOmeroRef, nfOmero)
        nfOmeroPath = f'$projectDir/{nfOmero.relative_to(outputPath)}'

        return biitConfigPath, nfProcessPath, nfListFilesPath, nfOmeroPath, condaPath
    
    def exportNextFlowGraph(self):
        graphManager = self.pyFlowInstance.graphManager.get()
        nodes = graphManager.getAllNodes()
        RunTool.createUuidToNodes(nodes)
        assert(all(isinstance(n, BiitArrayNodeBase) or isinstance(n, ListFiles) or isinstance(n, OmeroBase) for n in nodes))
        for node in nodes:
            node.processNode(True)
        nodesToProcess = set([n for n in nodes if isinstance(n, BiitArrayNodeBase) or isinstance(n, ListFiles) or isinstance(n, OmeroBase)])

        biitConfigPath, _, _, _, condaPath = self.copyDependencies(graphManager)

        processes = {}
        executions = []
        while len(nodesToProcess)>0:
            lastN = len(nodesToProcess)
            for node in nodesToProcess.copy():
                if not self.inputsWereProcessed(node, nodesToProcess): continue
                self.exportNextFlowNode(node, processes, executions)
                nodesToProcess.remove(node)
            if len(nodesToProcess) == lastN:
                QMessageBox.warning(self.pyFlowInstance, "Cycle in the graph", "There is a cycle in the graph, some nodes cannot be executed.")
                return

        workflow = f'params.conda_path = "{condaPath}"\n'
        workflow += f'params.biit_config_path = "{biitConfigPath}"\n\n'
        workflow += '\n'.join([p for p in processes.values()])
        workflow += '\nworkflow {\n'
        workflow += '\n'.join(['\t' + e for e in executions])
        workflow += '\n}'
        
        return workflow

    def exportNextFlow(self):
        graphManager = self.pyFlowInstance.graphManager.get()
        with open(Path(graphManager.workflowPath) / 'workflow.nf', "w") as f:
            f.write(self.exportNextFlowGraph())

    def do(self):
        self.exportNextFlow()