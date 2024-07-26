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
import subprocess
import pandas
import os
from multiprocessing.connection import Client

from qtpy import QtCore, QtGui
from qtpy.QtWidgets import QTableView, QLabel, QVBoxLayout, QWidget

from PyFlow import getRootPath
from PyFlow.UI.Tool.Tool import DockTool
from PyFlow.ToolManagement.EnvironmentManager import environmentManager
from PyFlow.Packages.PyFlowBase.Tools.PandasModel import PandasModel
from PyFlow.ConfigManager import ConfigManager
from PyFlow.Packages.PyFlowBase.Tools.ThumbnailGenerator import thumbnailGenerator
# from PyFlow.Viewer.NapariManager import NapariManager
from PyFlow.Viewer import environment, dependencies
try:
	from PyFlow.Packages.PyFlowBase.Tools.ImageViewerTool import ImageViewerTool
except ImportError as e:
	ImageViewerTool = None

class TableTool(DockTool):
	"""docstring for Table tool."""

	napariEnvironment = None
	nTries = 0

	def __init__(self):
		super(TableTool, self).__init__()
		self.content = None
		thumbnailGenerator.finished.connect(self.updateThumbnails)

	def onShow(self):
		super(TableTool, self).onShow()
		self.setMinimumSize(QtCore.QSize(200, 50))
		self.container = QWidget()
		self.layout:QVBoxLayout = QVBoxLayout()
		self.label = QLabel()
		self.label.hide()
		self.layout.addWidget(self.label)

		self.content = QTableView()
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
		napariEnvironment = ConfigManager().getPrefsValue("PREFS", "General/ImageViewerCmd")
		env = os.environ.copy()
		# Uset the QT_API so that napari finds the QT version of the conda env
		if 'QT_API' in env:
			del env['QT_API']

		napariEnvironment = napariEnvironment if len(napariEnvironment)>0 else environment
		napariManagerPath = getRootPath() / 'Viewer' / 'NapariManager.py'
		self.napariEnvironment = environmentManager.createAndLaunch(napariEnvironment, dependencies, customCommand=f'python -u "{napariManagerPath}"', environmentVariables=env)

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
	
	def onTableClicked(self, item):
		imageViewerOpened = ImageViewerTool is not None and any([isinstance(toolInstance, ImageViewerTool) for toolInstance in self.pyFlowInstance._tools])
		imageViewer = self.pyFlowInstance.getRegisteredTools(classNameFilters=["ImageViewerTool"])
		
		imageViewerCmd = ConfigManager().getPrefsValue("PREFS", "General/ImageViewerCmd")
		path = item.data(QtCore.Qt.UserRole)
		if not imageViewerOpened and len(imageViewerCmd)>0:
			# imageViewerCmd = imageViewerCmd.replace("@FILE", str(path))
			# subprocess.Popen([imageViewerCmd, str(path)])

			# env = os.environ.copy()
			# # Uset the QT_API so that napari finds the QT version of the conda env
			# if 'QT_API' in env:
			#     del env['QT_API']
			# environmentManager._executeCommands([environmentManager._activateConda(), f'conda activate {imageViewerCmd}', f'napari {path}'], env=env)
			
			removeExistingImages = not QtGui.QGuiApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier

			self.openImageOnNapari(path, removeExistingImages)

		elif len(imageViewer)>0:
			if isinstance(path, Path):
				if not QtGui.QGuiApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier:
					imageViewer[0].clear()
				imageViewer[0].open(path)
	
	def updateTable(self, node):
		data = None
		if hasattr(node._rawNode, 'outArray'):
			node._rawNode.compute()
			node._rawNode.afterCompute()
			data = node._rawNode.outArray.currentData()
		elif hasattr(node._rawNode, 'inArray'):
			data = node._rawNode.inArray.currentData()
		self.label.hide()
		if hasattr(node._rawNode, 'outputMessage') and node._rawNode.outputMessage is not None:
			self.label.setText(node._rawNode.outputMessage)
			self.label.show()
		if data is not None:
			if self.content is not None and isinstance(data, pandas.DataFrame):
				self.setData(data)
		else:
			self.setData()

	def setData(self, data=None):
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
		return QtCore.Qt.RightDockWidgetArea

	@staticmethod
	def toolTip():
		return "Current Data Frame"

	@staticmethod
	def name():
		return "Data frame"
