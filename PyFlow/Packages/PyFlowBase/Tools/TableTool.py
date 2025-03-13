from pathlib import Path
import pandas
import os

from qtpy import QtCore, QtGui
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import QTableView, QLabel, QVBoxLayout, QWidget, QProgressDialog, QMessageBox

from PyFlow import getSourcesPath
from PyFlow.invoke_in_main import inthread, inmain
from PyFlow.UI.Tool.Tool import DockTool
from PyFlow.ToolManagement.EnvironmentManager import environmentManager
from PyFlow.Packages.PyFlowBase.Tools.PandasModel import PandasModel
from PyFlow.ConfigManager import ConfigManager
from PyFlow.ThumbnailManagement.ThumbnailGenerator import ThumbnailGenerator
# from PyFlow.Viewer.NapariManager import NapariManager
from PyFlow.Viewer import environment, dependencies
try:
	from PyFlow.Packages.PyFlowBase.Tools.ImageViewerTool import ImageViewerTool
except ImportError as e:
	ImageViewerTool = None


class BiitTableView(QTableView):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setMouseTracking(True)
		self.viewport().installEventFilter(self)

	def eventFilter(self, obj, event):
		if obj == self.viewport() and event.type() == QtCore.QEvent.MouseMove:
			index = self.indexAt(event.pos())
			if index.isValid() and isinstance(self.model().data(index, QtCore.Qt.DisplayRole), QPixmap):
				self.viewport().setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
			else:
				self.viewport().unsetCursor()
		return super().eventFilter(obj, event)
		
class TableTool(DockTool):
	"""docstring for Table tool."""

	napariEnvironment = None
	nTries = 0

	def __init__(self):
		super(TableTool, self).__init__()
		self.content = None
		ThumbnailGenerator.get().finished.connect(self.updateThumbnails)

	def onShow(self):
		super(TableTool, self).onShow()
		self.setMinimumSize(QtCore.QSize(200, 50))
		self.openImageProgressDialog = None
		self.container = QWidget()
		self.layout:QVBoxLayout = QVBoxLayout()
		self.label = QLabel()
		self.label.hide()
		self.layout.addWidget(self.label)

		self.content = BiitTableView()
		self.content.resize(800, 500)
		self.content.horizontalHeader().setStretchLastSection(True)
		self.content.setAlternatingRowColors(True)
		self.content.setSelectionBehavior(QTableView.SelectRows)
		
		self.setData()
		self.content.show()
		self.content.setObjectName("TableToolContent")
		# self.setWidget(self.content)
		self.layout.addWidget(self.content)
		self.container.setLayout(self.layout)
		self.setWidget(self.container)
		self.content.clicked.connect(self.onTableClicked)


	def launchNapari(self):
		env = os.environ.copy()
		# Uset the QT_API so that napari finds the QT version of the conda env
		if 'QT_API' in env:
			del env['QT_API']

		napariEnvironment = ConfigManager().getPrefsValue("PREFS", "General/ImageViewerCmd")
		napariEnvironment = napariEnvironment if isinstance(napariEnvironment, str) and len(napariEnvironment) > 0 else environment
		napariManagerPath = getSourcesPath() / 'PyFlow' / 'Viewer' / 'NapariManager.py'
		if self.openImageProgressDialog is not None and not environmentManager.environmentIsLaunched(napariEnvironment):
			inmain(lambda: self.openImageProgressDialog.setLabelText('Installing and launching napari...\nThis could take a few minutes.'))
		self.napariEnvironment = environmentManager.createAndLaunch(napariEnvironment, dependencies, customCommand=f'python -u "{napariManagerPath}"', environmentVariables=env)
		if self.openImageProgressDialog is not None:
			inmain(lambda: self.openImageProgressDialog.setLabelText('Opening image...'))

	def tryOpenImageOnNapari(self, path, removeExistingImages):
		self.launchNapari()
		try:
			self.napariEnvironment.connection.send((str(path), removeExistingImages))
		except (EOFError, BrokenPipeError) as e:
			if self.nTries>1:
				raise e
			self.nTries += 1
			environmentManager.exit(self.napariEnvironment)
			self.tryOpenImageOnNapari(path, removeExistingImages)

	def openImageOnNapari(self, path, removeExistingImages):
		self.nTries = 0
		self.tryOpenImageOnNapari(path, removeExistingImages)
	
	def openImageAndClose(self, path, removeExistingImages, progress):
		self.checkIfNodesMustInstallViewerDependencies()
		self.openImageOnNapari(path, removeExistingImages)
		inmain(lambda: progress.close())
	
	def askConfirmInstallViewerDependencies(self, node, dependenciesString):
		alwaysInstallDependencies = ConfigManager().getPrefsValue("PREFS", "General/ImageViewerAlwaysInstallDependencies")
		if alwaysInstallDependencies != None and alwaysInstallDependencies != 'None' and str(alwaysInstallDependencies).lower() != 'unknown':
			return alwaysInstallDependencies == 'Yes'
		btn = QMessageBox.warning(self, "Install Napari dependencies?", f'The node "{node.name}" requires {dependenciesString} dependencies. Would you like to always install dependencies in the environment "{self.napariEnvironment.name}" when necessary? You can change this choice later in the Preferences panel > General > Always Install Napari Dependencies.', QMessageBox.Yes | QMessageBox.No)
		ConfigManager().setPrefsValue("PREFS", "General/ImageViewerAlwaysInstallDependencies", 'Yes' if btn == QMessageBox.Yes else 'No')
		return btn == QMessageBox.Yes
	
	def installViewerDependencies(self, node, dependencies):
		self.launchNapari()
		if not environmentManager.dependenciesAreInstalled(self.napariEnvironment.name, dependencies):
			hasPipDependencies = 'pip' in dependencies and len(dependencies['pip']) > 0
			hasCondaDependencies = 'conda' in dependencies and len(dependencies['conda']) > 0
			dependenciesString = f"pip ({', '.join(dependencies['pip'])})" if hasPipDependencies else ''
			dependenciesString += ' and ' if hasPipDependencies and hasCondaDependencies else ''
			dependenciesString += f"conda ({', '.join(dependencies['conda'])})" if hasCondaDependencies else ''
			if not inmain(lambda: self.askConfirmInstallViewerDependencies(node, dependenciesString)):
				return
			if self.openImageProgressDialog is not None:
				inmain(lambda: self.openImageProgressDialog.setLabelText(f'Installing {dependenciesString} dependencies in Napari...\nThis could take a few minutes.'))
			installDepsCommands = environmentManager.installDependencies(self.napariEnvironment.name, dependencies, True)
			environmentManager.executeCommands(environmentManager._activateConda() + installDepsCommands, waitComplete=True)
			if self.openImageProgressDialog is not None:
				inmain(lambda: self.openImageProgressDialog.setLabelText('Opening image...'))
	
	def checkIfNodesMustInstallViewerDependencies(self):
		graphManager = self.pyFlowInstance.graphManager.get()
		nodes = graphManager.getAllNodes()
		for node in nodes:
			if hasattr(node, 'Tool') and 'viewer' in node.Tool.dependencies:
				self.installViewerDependencies(node, node.Tool.dependencies['viewer'])
		return
	
	def onTableClicked(self, item):
		imageViewerOpened = ImageViewerTool is not None and any([isinstance(toolInstance, ImageViewerTool) for toolInstance in self.pyFlowInstance._tools])
		imageViewer = self.pyFlowInstance.getRegisteredTools(classNameFilters=["ImageViewerTool"])
		
		path = item.data(QtCore.Qt.UserRole)
		if path is None: return
		if not imageViewerOpened:
			
			removeExistingImages = not QtGui.QGuiApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier
			
			self.openImageProgressDialog = QProgressDialog(labelText='Opening image...', cancelButtonText='Cancel', minimum=0, maximum=0, parent=self.pyFlowInstance)
			self.openImageProgressDialog.setWindowModality(QtCore.Qt.WindowModal)
			self.openImageProgressDialog.setWindowTitle('Opening Napari')

			self.openImageProgressDialog.setMinimumDuration(500)
			self.openImageProgressDialog.setValue(0)
			inthread(self.openImageAndClose, path, removeExistingImages, self.openImageProgressDialog)

		elif len(imageViewer)>0:
			if isinstance(path, Path):
				if not QtGui.QGuiApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier:
					imageViewer[0].clear()
				imageViewer[0].open(path)
	
	def updateTable(self, node):
		node._rawNode.processNode()
		data = None
		if hasattr(node._rawNode, 'outArray'):
			data = node._rawNode.outArray.currentData()
		elif hasattr(node._rawNode, 'inArray'):
			data = node._rawNode.inArray.currentData()
		self.label.hide()
		if hasattr(node._rawNode, 'outputMessage') and node._rawNode.outputMessage is not None:
			self.label.setText(node._rawNode.outputMessage)
			self.label.show()
		self.setData(data)

	def setData(self, data=None):
		if self.content is None: return
		if (data is not None) and not isinstance(data, pandas.DataFrame): return
		self.content.setModel(PandasModel(data))
		# self.content.setItemDelegate(ImageDelegate(self))
		self.content.resizeRowsToContents()
		self.content.model().rowsInserted.connect(lambda: self.content.resizeRowsToContents())
		return
	
	def resizeRows(self):
		self.content.resizeRowsToContents()

	def updateThumbnails(self, results):
		print('updateThumbnails')
		if self.content is None or self.content.model is None: return
		self.content.model().layoutChanged.emit()
	
	def clear(self):
		self.setData()
	
	@staticmethod
	def isSingleton():
		return True

	@staticmethod
	def defaultDockArea():
		return QtCore.Qt.BottomDockWidgetArea

	@staticmethod
	def toolTip():
		return "Current Data Frame"

	@staticmethod
	def name():
		return "Data frame"
