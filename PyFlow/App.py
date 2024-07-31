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


"""Application class here
"""

import os
import json
import shutil
from string import ascii_letters
import random
from pathlib import Path

from qtpy import QtGui
from qtpy import QtCore
from qtpy.QtCore import QMetaMethod
from qtpy.QtWidgets import *
from qtpy.QtWidgets import QMessageBox

from PyFlow import GET_PACKAGES
from PyFlow.UpdateManager import UpdateManager
from PyFlow.Core.PathsRegistry import PathsRegistry
from PyFlow.Core.version import *
from PyFlow.Core.GraphManager import GraphManagerSingleton
from PyFlow.Core.Common import currentProcessorTime
from PyFlow.Core.Common import SingletonDecorator
from PyFlow.Core.Common import validateGraphDataPackages
from PyFlow.UI.Canvas.UICommon import SessionDescriptor
from PyFlow.UI.Widgets.BlueprintCanvas import BlueprintCanvasWidget
from PyFlow.UI.Tool.Tool import ShelfTool, DockTool
from PyFlow.UI.EditorHistory import EditorHistory
from PyFlow.UI.Tool import GET_TOOLS
from PyFlow.UI.Utils.stylesheet import editableStyleSheet
from PyFlow.UI.ContextMenuGenerator import ContextMenuGenerator
from PyFlow.UI.Widgets.PreferencesWindow import PreferencesWindow

try:
	from PyQtAds import QtAds
except ImportError:
	import PySide6QtAds as QtAds

try:
	from PyFlow.Packages.PyFlowBase.Tools.PropertiesTool import PropertiesTool
	from PyFlow.Packages.PyFlowBase.Tools.TableTool import TableTool
	from PyFlow.Packages.PyFlowBase.Tools.WorkflowTool import WorkflowTool
except ImportError as e:
	print(e)
	pass
import asyncio

import PyFlow.UI.resources
# from PyFlow.Wizards.PackageWizard import PackageWizard

from PyFlow import INITIALIZE
from PyFlow.Input import InputAction, InputActionType
from PyFlow.Input import InputManager
from PyFlow.ConfigManager import ConfigManager
from PyFlow.Core.OmeroService import OmeroService

import PyFlow.UI.resources

EDITOR_TARGET_FPS = 30


def generateRandomString(numbSymbols=5):
	result = ""
	for i in range(numbSymbols):
		letter = random.choice(ascii_letters)
		result += letter
	return result


def getOrCreateMenu(menuBar, title):
	for child in menuBar.findChildren(QMenu):
		if child.title() == title:
			return child
	menu = QMenu(menuBar)
	menu.setObjectName(title)
	menu.setTitle(title)
	return menu


def winTitle():
	return "BioImageIT v{0}".format(currentVersion().__str__())


# App itself
class PyFlow(QMainWindow):

	appInstance = None

	newFileExecuted = QtCore.Signal(bool)
	fileBeenLoaded = QtCore.Signal()

	def __init__(self, parent=None):
		super(PyFlow, self).__init__(parent=parent)
		self._modified = False
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.currentSoftware = ""
		self.edHistory = EditorHistory(self)
		self.edHistory.statePushed.connect(self.historyStatePushed)
		self.setWindowTitle(winTitle())
		self.undoStack = QtGui.QUndoStack(self)
		self.setContentsMargins(1, 1, 1, 1)
		self.graphManager = GraphManagerSingleton()
		self.canvasWidget = BlueprintCanvasWidget(self.graphManager.get(), self)
		self.canvasWidget.setObjectName("canvasWidget")
		# self.setCentralWidget(self.canvasWidget)
		# self.setTabPosition(QtCore.Qt.AllDockWidgetAreas, QTabWidget.North)
		# self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks)

		# // Create the dock manager after the ui is setup. Because the
		# // parent parameter is a QMainWindow the dock manager registers
		# // itself as the central widget as such the ui must be set up first.
		QtAds.CDockManager.setConfigFlags(QtAds.CDockManager.DefaultOpaqueConfig)
		self.dockManager: QtAds.CDockManager = QtAds.CDockManager(self)
		# self.dockManager.setStyleSheet(str(Path(__file__).parent / 'ads.css'))

		self.canvasDockWidget = QtAds.CDockWidget("Canvas")
		self.canvasDockWidget.setWidget(self.canvasWidget)
		centralDockArea = self.dockManager.setCentralWidget(self.canvasDockWidget)

		self.dockAreas = {}
		self.dockAreasByToolName = {}
		self.dockAreas[QtAds.BottomDockWidgetArea] = centralDockArea

		self.menuBar = QMenuBar(self)
		self.menuBar.setGeometry(QtCore.QRect(0, 0, 863, 21))
		self.menuBar.setObjectName("menuBar")
		self.setMenuBar(self.menuBar)
		# self.toolBar = QToolBar(self)
		# self.toolBar.setObjectName("toolBar")
		# self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

		self.setWindowIcon(QtGui.QIcon(":/LogoBpApp.png"))
		self._tools = set()
		self.currentTempDir = ""

		self.preferencesWindow = PreferencesWindow(self)
		self.preferencesWindow.settingsUpdated.connect(OmeroService().reset)
		self.preferencesWindow.settingsUpdated.connect(UpdateManager.get().initializeAutoUpdate)
		UpdateManager.get().versionInstalled.connect(self.warnNewVersion)

		self.setMouseTracking(True)

		self._lastClock = 0.0
		self.fps = EDITOR_TARGET_FPS
		self.tick_timer = QtCore.QTimer()
		self._currentFileName = ""
		self.currentFileName = None

	def warnNewVersion(self):
		self.updatingVersion = False
		answer = QMessageBox.warning(self, "New BioImageIT version", "A new version of BioImageIT was just installed, please restart the application to take changes into account. Would you like to quit BioImageIT?", QMessageBox.Yes | QMessageBox.No)
		if answer == QMessageBox.Yes:
			if self.restartApp is not None:
				self.restartApp()
			else:
				self.close()

	def historyStatePushed(self, state):
		if state.modifiesData():
			self.modified = True
			self.updateLabel()
		# print(state, state.modifiesData())

	@property
	def modified(self):
		return self._modified

	@modified.setter
	def modified(self, value):
		self._modified = value
		self.updateLabel()

	def updateLabel(self):
		label = "Untitled"
		if self.currentFileName is not None:
			if os.path.isfile(self.currentFileName):
				label = os.path.basename(self.currentFileName)
		if self.modified:
			label += "*"
		self.setWindowTitle("{0} - {1}".format(winTitle(), label))

	def getMenuBar(self):
		return self.menuBar

	def getWorkflowTool(self)-> WorkflowTool:
		for toolInstance in self._tools:
			if isinstance(toolInstance, WorkflowTool):
				return toolInstance
	
	def populateMenu(self, fileMenu):

		newFileAction = fileMenu.addAction("New workflow")
		newFileAction.setIcon(QtGui.QIcon(":/new_file_icon.png"))
		newFileAction.triggered.connect(self.getWorkflowTool().createWorkflow)

		loadAction = fileMenu.addAction("Open workflow")
		loadAction.setIcon(QtGui.QIcon(":/folder_open_icon.png"))
		loadAction.triggered.connect(self.getWorkflowTool().openWorkflow)

		saveAction = fileMenu.addAction("Save workflow")
		saveAction.setIcon(QtGui.QIcon(":/save_icon.png"))
		saveAction.triggered.connect(self.save)

		saveAsAction = fileMenu.addAction("Export workflow")
		saveAsAction.setIcon(QtGui.QIcon(":/save_as_icon.png"))
		saveAsAction.triggered.connect(self.getWorkflowTool().exportWorkflow)

		# IOMenu = fileMenu.addMenu("Custom IO")
		# for packageName, package in GET_PACKAGES().items():
		#     # exporters
		#     try:
		#         exporters = package.GetExporters()
		#     except:
		#         continue
		#     pkgMenu = IOMenu.addMenu(packageName)
		#     for exporterName, exporterClass in exporters.items():
		#         fileFormatMenu = pkgMenu.addMenu(exporterClass.displayName())
		#         fileFormatMenu.setToolTip(exporterClass.toolTip())
		#         if exporterClass.createExporterMenu():
		#             exportAction = fileFormatMenu.addAction("Export")
		#             exportAction.triggered.connect(
		#                 lambda checked=False, app=self, exporter=exporterClass: exporter.doExport(
		#                     app
		#                 )
		#             )
		#         if exporterClass.createImporterMenu():
		#             importAction = fileFormatMenu.addAction("Import")
		#             importAction.triggered.connect(
		#                 lambda checked=False, app=self, exporter=exporterClass: exporter.doImport(
		#                     app
		#                 )
		#             )

		# editMenu = self.menuBar.addMenu("Edit")
		preferencesAction = fileMenu.addAction("Preferences")
		preferencesAction.setIcon(QtGui.QIcon(":/options_icon.png"))
		preferencesAction.triggered.connect(self.showPreferencesWindow)

		# pluginsMenu = self.menuBar.addMenu("Plugins")
		# packagePlugin = pluginsMenu.addAction("Create package...")
		# packagePlugin.triggered.connect(PackageWizard.run)

		helpMenu = self.menuBar.addMenu("Help")
		helpMenu.addAction("Homepage").triggered.connect(
			lambda _=False, url="https://bioimageit.github.io/": QtGui.QDesktopServices.openUrl(
				url
			)
		)
		helpMenu.addAction("Docs").triggered.connect(
			lambda _=False, url="https://bioimageit.github.io/": QtGui.QDesktopServices.openUrl(
				url
			)
		)

	def showPreferencesWindow(self):
		self.preferencesWindow.show()

	def registerToolInstance(self, instance):
		"""Registers tool instance reference

		This needed to prevent classes from being garbage collected and to save widgets state

		Args:

			instance (ToolBase): Tool to be registered
		"""
		self._tools.add(instance)

	def unregisterToolInstance(self, instance):
		if instance in self._tools:
			self._tools.remove(instance)

	def onRequestFillProperties(self, propertiesFillDelegate):
		for toolInstance in self._tools:
			if isinstance(toolInstance, PropertiesTool):
				toolInstance.clear()
				toolInstance.assignPropertiesWidget(propertiesFillDelegate)

	def onRequestClearProperties(self):
		for toolInstance in self._tools:
			if isinstance(toolInstance, PropertiesTool):
				toolInstance.clear()

	def onRequestFillTable(self, node):
		for toolInstance in self._tools:
			if isinstance(toolInstance, TableTool):
				toolInstance.updateTable(node)

	def onRequestClearTable(self):
		for toolInstance in self._tools:
			if isinstance(toolInstance, TableTool):
				toolInstance.clear()

	# def getToolbar(self):
	#     return self.toolBar

	def getCanvas(self):
		return self.canvasWidget.canvas

	def keyPressEvent(self, event):
		modifiers = event.modifiers()
		currentInputAction = InputAction(
			name="temp",
			actionType=InputActionType.Keyboard,
			key=event.key(),
			modifiers=modifiers,
		)

		actionSaveVariants = InputManager()["App.Save"]
		actionNewFileVariants = InputManager()["App.NewFile"]
		actionLoadVariants = InputManager()["App.Load"]
		actionSaveAsVariants = InputManager()["App.SaveAs"]

		if currentInputAction in actionNewFileVariants:
			shouldSave = self.shouldSave()
			if shouldSave == QMessageBox.Save:
				self.save()
			elif shouldSave == QMessageBox.Cancel:
				return

			EditorHistory().clear()
			historyTools = self.getRegisteredTools(classNameFilters=["HistoryTool"])
			for historyTools in historyTools:
				historyTools.onClear()
			self.newFile()
			EditorHistory().saveState("New file")
			self.currentFileName = None
			self.modified = False
			self.updateLabel()
		if currentInputAction in actionSaveVariants:
			self.save()
		if currentInputAction in actionLoadVariants:
			shouldSave = self.shouldSave()
			if shouldSave == QMessageBox.Save:
				self.save()
			elif shouldSave == QMessageBox.Discard:
				return
			self.load()
		if currentInputAction in actionSaveAsVariants:
			self.save(True)

	def loadFromFileChecked(self, filePath):
		shouldSave = self.shouldSave()
		if shouldSave == QMessageBox.Save:
			self.save()
		elif shouldSave == QMessageBox.Discard:
			return
		self.loadFromFile(filePath)
		self.modified = False
		self.updateLabel()

	def loadFromData(self, data, clearHistory=False):

		# check first if all packages we are trying to load are legal
		missedPackages = set()  # TODO: nothing fills this, can never report missing package
		if not validateGraphDataPackages(data, missedPackages):
			msg = "This graph can not be loaded. Following packages not found:\n\n"
			index = 1
			for missedPackageName in missedPackages:
				msg += "{0}. {1}\n".format(index, missedPackageName)
				index += 1
			QMessageBox.critical(self, "Missing dependencies", msg)
			return

		if clearHistory:
			EditorHistory().clear()
			historyTools = self.getRegisteredTools(classNameFilters=["HistoryTool"])
			for historyTools in historyTools:
				historyTools.onClear()

		self.newFile(keepRoot=False)
		# load raw data
		self.graphManager.get().deserialize(data)
		self.fileBeenLoaded.emit()
		self.graphManager.get().selectGraphByName(data["activeGraph"])
		self.updateLabel()
		PathsRegistry().rebuild()

	@property
	def currentFileName(self):
		return self._currentFileName

	@currentFileName.setter
	def currentFileName(self, value):
		self._currentFileName = value
		self.updateLabel()

	def loadFromFile(self, filePath):
		with open(filePath, "r") as f:
			data = json.load(f)
			self.loadFromData(data, clearHistory=True)
			self.currentFileName = filePath
			EditorHistory().saveState(
				"Open {}".format(os.path.basename(self.currentFileName))
			)

	def load(self):
		name_filter = "Graph files (*.pygraph)"
		savepath = QFileDialog.getOpenFileName(filter=name_filter)
		if type(savepath) in [tuple, list]:
			fpath = savepath[0]
		else:
			fpath = savepath
		if not fpath == "":
			self.loadFromFile(fpath)

	def updateCSS(self):
		with open(Path(__file__).parent / "app.css", "r") as style_sheet_file:
			QApplication.instance().setStyleSheet(style_sheet_file.read())

	def save(self, save_as=False):

		if save_as:
			name_filter = "Graph files (*.pygraph)"
			savepath = QFileDialog.getSaveFileName(filter=name_filter)
			if type(savepath) in [tuple, list]:
				pth = savepath[0]
			else:
				pth = savepath
			if not pth == "":
				self.currentFileName = pth
			else:
				self.currentFileName = None
		else:
			if self.currentFileName is None:
				name_filter = "Graph files (*.pygraph)"
				savepath = QFileDialog.getSaveFileName(filter=name_filter)
				if type(savepath) in [tuple, list]:
					pth = savepath[0]
				else:
					pth = savepath
				if not pth == "":
					self.currentFileName = pth
				else:
					self.currentFileName = None

		if not self.currentFileName:
			return False

		if not self.currentFileName.endswith(".pygraph"):
			self.currentFileName += ".pygraph"

		if not self.currentFileName == "":
			with open(self.currentFileName, "w") as f:
				saveData = self.graphManager.get().serialize()
				json.dump(saveData, f, indent=4)
			print(str("// saved: '{0}'".format(self.currentFileName)))
			self.modified = False
			self.updateLabel()
			return True

	def _clickNewFile(self):
		shouldSave = self.shouldSave()
		if shouldSave == QMessageBox.Save:
			
			self.save()
		elif shouldSave == QMessageBox.Cancel:
			return

		EditorHistory().clear()
		historyTools = self.getRegisteredTools(classNameFilters=["HistoryTool"])
		for historyTools in historyTools:
			historyTools.onClear()
		self.newFile()
		EditorHistory().saveState("New file")
		self.currentFileName = None
		self.modified = False
		self.updateLabel()
		
	def newFile(self, keepRoot=True):
		self.stopMainLoop()

		# broadcast
		self.graphManager.get().clear(keepRoot=keepRoot)

		self.newFileExecuted.emit(keepRoot)
		self.onRequestClearProperties()
		self.onRequestClearTable()

		self.startMainLoop()

	def startMainLoop(self):
		self.tick_timer.timeout.connect(self.mainLoop)
		self.tick_timer.start(1000 / EDITOR_TARGET_FPS)

	def stopMainLoop(self):
		self.tick_timer.stop()
		if self.tick_timer.isSignalConnected(QMetaMethod.fromSignal(self.tick_timer.timeout)):
			self.tick_timer.timeout.disconnect()

	def mainLoop(self):
		asyncio.get_event_loop().run_until_complete(self._tick_asyncio())
		
		deltaTime = currentProcessorTime() - self._lastClock
		ds = deltaTime * 1000.0
		if ds > 0:
			self.fps = int(1000.0 / ds)

		# Tick all graphs
		# each graph will tick owning raw nodes
		# each raw node will tick its ui wrapper if it exists
		self.graphManager.get().Tick(deltaTime)

		# Tick canvas. Update ui only stuff such animation etc.
		self.canvasWidget.Tick(deltaTime)

		self._lastClock = currentProcessorTime()
		
	async def _tick_asyncio(self):
		await asyncio.sleep(0.00001)

	def createPopupMenu(self):
		pass

	def getToolClassByName(self, packageName, toolName, toolClass=DockTool):
		registeredTools = GET_TOOLS()
		for ToolClass in registeredTools[packageName]:
			if issubclass(ToolClass, toolClass):
				if ToolClass.name() == toolName:
					return ToolClass
		return None

	def createToolInstanceByClass(self, packageName, toolName, toolClass=DockTool):
		registeredTools = GET_TOOLS()
		for ToolClass in registeredTools[packageName]:
			supportedSoftwares = ToolClass.supportedSoftwares()
			if "any" not in supportedSoftwares:
				if self.currentSoftware not in supportedSoftwares:
					continue

			if issubclass(ToolClass, toolClass):
				if ToolClass.name() == toolName:
					return ToolClass()
		return None

	def getRegisteredTools(self, classNameFilters=None):
		if classNameFilters is None:
			classNameFilters = []
		if len(classNameFilters) == 0:
			return self._tools
		else:
			result = []
			for tool in self._tools:
				if tool.__class__.__name__ in classNameFilters:
					result.append(tool)
			return result
	
	def getToolByClassName(self, name):
		tools = [tool for tool in self._tools if tool.name() == name]
		return tools[0] if len(tools)>0 else None

	def invokeDockToolByName(self, packageName, name, settings=None):
		# invokeDockToolByName Invokes dock tool by tool name and package name
		# If settings provided QMainWindow::restoreDockWidget will be called instead QMainWindow::addDockWidget
		toolClass = self.getToolClassByName(packageName, name, DockTool)
		if toolClass is None:
			return
		isSingleton = toolClass.isSingleton()
		# if isSingleton:
		# check if already registered
		if name in [t.name() for t in self._tools]:
			for tool in self._tools:
				if tool.name() == name:
					# tool.show()
					# tool.onShow()
					# Highlight window
					# print("highlight", tool.uniqueName())
					if tool.dockWidget.isClosed():
						tool.dockWidget.toggleView(True)
					return tool
		ToolInstance = self.createToolInstanceByClass(packageName, name, DockTool)
		if ToolInstance:
			if ToolInstance in self._tools: return ToolInstance
			self.registerToolInstance(ToolInstance)
			# if settings is not None:
			#     ToolInstance.restoreState(settings)
			#     # if not self.restoreDockWidget(ToolInstance):
			#     #     # handle if ui state was not restored
			#     #     pass
			# else:
			#     # self.addDockWidget(ToolInstance.defaultDockArea(), ToolInstance)
			#     ToolInstance.setAppInstance(self)
			#     ToolInstance.onShow()
			#     dockWidget = QtAds.CDockWidget(name)
			#     dockWidget.setWidget(ToolInstance.widget())
			#     qtToAdsAreas = {}
			#     qtToAdsAreas[QtCore.Qt.BottomDockWidgetArea] = QtAds.BottomDockWidgetArea
			#     qtToAdsAreas[QtCore.Qt.TopDockWidgetArea] = QtAds.TopDockWidgetArea
			#     qtToAdsAreas[QtCore.Qt.LeftDockWidgetArea] = QtAds.LeftDockWidgetArea
			#     qtToAdsAreas[QtCore.Qt.RightDockWidgetArea] = QtAds.RightDockWidgetArea
			#     self.dockManager.addDockWidget(qtToAdsAreas[ToolInstance.defaultDockArea()], dockWidget)
			ToolInstance.setAppInstance(self)
			ToolInstance.onShow()
			dockWidget = QtAds.CDockWidget(name)
			dockWidget.setWidget(ToolInstance.widget())
			qtToAdsAreas = {}
			qtToAdsAreas[QtCore.Qt.BottomDockWidgetArea] = QtAds.BottomDockWidgetArea
			qtToAdsAreas[QtCore.Qt.TopDockWidgetArea] = QtAds.TopDockWidgetArea
			qtToAdsAreas[QtCore.Qt.LeftDockWidgetArea] = QtAds.LeftDockWidgetArea
			qtToAdsAreas[QtCore.Qt.RightDockWidgetArea] = QtAds.RightDockWidgetArea
			area = qtToAdsAreas[ToolInstance.defaultDockArea()]
			subArea = ToolInstance.defaultSubDockArea() if type(ToolInstance.defaultSubDockArea()) is str else qtToAdsAreas[ToolInstance.defaultSubDockArea()]
			dockWidget.setFeature(QtAds.CDockWidget.DockWidgetClosable, ToolInstance.isClosable())
			dockWidget.setFeature(QtAds.CDockWidget.DockWidgetMovable, ToolInstance.isMovable())
			dockWidget.setFeature(QtAds.CDockWidget.DockWidgetFloatable, ToolInstance.isMovable())
			
			if type(subArea) is str:
				sas = subArea.split(':')
				if sas[0] == 'Tab':
					area = self.dockAreasByToolName[sas[1]]
					area.insertDockWidget(area.dockWidgetsCount(), dockWidget, False)
					area.setCurrentIndex(0)
			else:
				self.dockAreas[area] = self.dockManager.addDockWidget(area if area not in self.dockAreas else subArea, dockWidget, self.dockAreas[area] if area in self.dockAreas else None)
				self.dockAreasByToolName[name] = self.dockAreas[area]
			ToolInstance.dockWidget = dockWidget
			# dockWidget.closed.connect(lambda: )
		return ToolInstance

	def shouldSave(self):
		if self.modified:
			btn = QMessageBox.warning(
				self,
				"Confirm?",
				"Unsaved data will be lost. Save?",
				QMessageBox.Save | QMessageBox.Cancel | QMessageBox.Discard,
			)
			return btn
		return QMessageBox.Discard

	def closeEvent(self, event):
		shouldSave = self.shouldSave()
		if shouldSave == QMessageBox.Save:
			if not self.save():
				event.ignore()
				return
		elif shouldSave == QMessageBox.Cancel:
			event.ignore()
			return

		self.stopMainLoop()
		EditorHistory().shutdown()

		self.canvasWidget.shoutDown()
		# save editor config
		settings = ConfigManager().getSettings("APP_STATE")

		# clear file each time to capture opened dock tools
		settings.clear()
		settings.sync()

		settings.beginGroup("Editor")
		settings.setValue("geometry", self.saveGeometry())
		settings.setValue("state", self.saveState())
		settings.endGroup()

		# save tools state
		settings.beginGroup("Tools")
		for tool in self._tools:
			if isinstance(tool, ShelfTool):
				settings.beginGroup("ShelfTools")
				settings.beginGroup(tool.name())
				tool.saveState(settings)
				settings.endGroup()
				settings.endGroup()
			# if isinstance(tool, DockTool):
			#     settings.beginGroup("DockTools")
			#     settings.beginGroup(tool.uniqueName())
			#     tool.saveState(settings)
			#     settings.endGroup()
			#     settings.endGroup()
			tool.onDestroy()
		settings.endGroup()
		settings.sync()

		# remove temp directory if exists
		if os.path.exists(self.currentTempDir):
			shutil.rmtree(self.currentTempDir)

		SingletonDecorator.destroyAll()

		PyFlow.appInstance = None

		QMainWindow.closeEvent(self, event)

	@staticmethod
	def instance(parent=None, software="", restart=None):
		assert (
			software != ""
		), "Invalid arguments. Please pass you software name as second argument!"
		settings = ConfigManager().getSettings("APP_STATE")

		instance = PyFlow(parent)
		instance.currentSoftware = software
		SessionDescriptor().software = instance.currentSoftware
		instance.restartApp = restart

		if software == "standalone":
			editableStyleSheet(instance)

		try:
			extraPackagePaths = []
			extraPathsString = '' #ConfigManager().getPrefsValue("PREFS", "General/ExtraPackageDirs")
			if extraPathsString is not None:
				extraPathsString = extraPathsString.rstrip(";")
				extraPathsRaw = extraPathsString.split(";")
				for rawPath in extraPathsRaw:
					if os.path.exists(rawPath):
						extraPackagePaths.append(os.path.normpath(rawPath))
			INITIALIZE(additionalPackageLocations=extraPackagePaths, software=software)
		except Exception as e:
			QMessageBox.critical(None, "Fatal error", str(e))
			return

		instance.startMainLoop()
		# populate tools
		# toolbar = instance.getToolbar()

		# populate menus
		

		geo = settings.value("Editor/geometry")
		if geo is not None:
			instance.restoreGeometry(geo)
		state = settings.value("Editor/state")
		if state is not None:
			instance.restoreState(state)
		
		fileMenu = instance.menuBar.addMenu("File")
		toolsMenu = instance.menuBar.addMenu('Tools')

		settings.beginGroup("Tools")
		for packageName, registeredToolSet in GET_TOOLS().items():
			for ToolClass in registeredToolSet:
				if issubclass(ToolClass, ShelfTool):
					ToolInstance = ToolClass()
					# prevent to be garbage collected
					instance.registerToolInstance(ToolInstance)
					ToolInstance.setAppInstance(instance)
					action = QAction(instance)
					action.setIcon(ToolInstance.getIcon())
					action.setText(ToolInstance.name())
					action.setToolTip(ToolInstance.toolTip())
					action.setObjectName(ToolInstance.name())
					action.triggered.connect(ToolInstance.do)
					# check if context menu data available
					menuBuilder = ToolInstance.contextMenuBuilder()
					if menuBuilder:
						menuGenerator = ContextMenuGenerator(menuBuilder)
						menu = menuGenerator.generate()
						action.setMenu(menu)
					# toolbar.addAction(action)

					# step to ShelfTools/ToolName group and pass settings inside
					settings.beginGroup("ShelfTools")
					settings.beginGroup(ToolClass.name())
					ToolInstance.restoreState(settings)
					settings.endGroup()
					settings.endGroup()

				if issubclass(ToolClass, DockTool):
					# menus = instance.menuBar.findChildren(QMenu)
					# pluginsMenuAction = [m for m in menus if m.title() == "Plugins"][
					#     0
					# ].menuAction()
					# instance.menuBar.insertMenu(toolsMenu)
					# instance.menuBar.insertMenu(pluginsMenuAction, toolsMenu)
					# packageSubMenu = getOrCreateMenu(toolsMenu, packageName)
					# toolsMenu.addMenu(packageSubMenu)
					showToolAction = toolsMenu.addAction(ToolClass.name())
					icon = ToolClass.getIcon()
					if icon:
						showToolAction.setIcon(icon)
					showToolAction.triggered.connect(
						lambda checked, pkgName=packageName, toolName=ToolClass.name(): instance.invokeDockToolByName(
							pkgName, toolName
						) if not checked else None
					)

					settings.beginGroup("DockTools")
					childGroups = settings.childGroups()
					for dockToolGroupName in childGroups:
						# This dock tool data been saved on last shutdown
						settings.beginGroup(dockToolGroupName)
						if dockToolGroupName in [
							t.uniqueName() for t in instance._tools
						]:
							settings.endGroup()
							continue
						toolName = dockToolGroupName.split("::")[0]
						instance.invokeDockToolByName(packageName, toolName, settings)
						settings.endGroup()
					settings.endGroup()
		
		PyFlow.appInstance = instance

		# for toolName in ['Workflow', 'Tools', 'Properties', 'Table viewer', 'Logger']:
		for toolName in ['Tools', 'Workflow', 'Execution', 'Properties', 'Data frame']:
			tool = instance.getToolByClassName(toolName)
			if tool is None or toolName == 'Logger':
				instance.invokeDockToolByName("PyFlowBase", toolName)
		
		instance.populateMenu(fileMenu)

		EditorHistory().saveState("New file")

		for name, package in GET_PACKAGES().items():
			prefsWidgets = package.PrefsWidgets()
			if prefsWidgets is not None:
				for categoryName, widgetClass in prefsWidgets.items():
					PreferencesWindow().addCategory(categoryName, widgetClass())
				PreferencesWindow().selectByName("General")
		return instance
